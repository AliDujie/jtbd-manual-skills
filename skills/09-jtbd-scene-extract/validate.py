#!/usr/bin/env python3
"""JTBD 27/35列格式校验；不验证访谈真实性或评分证据。

python3 validate.py 场景库.md [--draft] [--fix]
python3 validate.py 旧33列.md --migrate-33
退出码：0=严格格式通过（仍须证据审校），1=错误，2=草稿/参数错误。
--fix 只改明确的阶段同义词，独占创建 *_fixed 文件，不覆盖原文/已有输出。
--migrate-33 按字段名迁移，新两列留空，独占创建 *_35_draft.md。
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

BASE_HEADERS = '序号、用户ID、用户档案、内容范围、是否出境游、情境标签、进步阶段、用户具体场景、进步陈述、当前主要方案、曾尝试或放弃的方案、是否补偿行为、补偿行为描述、切换触发点、爽点、痛点、情绪状态、推力P、拉力L、焦虑A、焦虑子类型、惯性I、惯性子类型、关键原话、改进方向、场景总分、质量分明细'.split('、')
ODI_HEADERS = 'Outcome Statement、Job Map阶段、Job维度、创新信号强度、创新信号类型、竞争关系、付费意愿信号、频次信号'.split('、')
HEADERS = BASE_HEADERS + ODI_HEADERS
LEGACY_HEADERS = BASE_HEADERS + [h for h in ODI_HEADERS if h not in ('创新信号类型', '竞争关系')]
VALID_STAGES = {'想象', '搜索', '使用', '实现'}
VALID_ANXIETY_SUB = VALID_INERTIA_SUB = {'选择', '使用', ''}
VALID_JOB_MAP = {'Define', 'Locate', 'Prepare', 'Confirm', 'Execute', 'Monitor', 'Modify', 'Conclude'}
VALID_JOB_DIM = {'Core Functional', 'Related', 'Emotional', 'Social', 'Financial', 'Consumption Chain', 'Context'}
VALID_INN_TYPE = {'补偿行为', '非消费', '不满意使用', '异常使用', '情境变化', '无'}
VALID_COMPETE = {'直接', '间接', '不用方案', '无'}
VALID_WTP = {'是', '否', '未提及'}
VALID_FREQ = {'日', '周', '月', '偶尔', '未提及'}
OS_VERBS = ('减少', '降低', '提升', '增加', '维持', '消除')
ANTI_INFLATION_MIN_N = 20
# 只保留定义明确的同义词；不据“财务风险”等标签猜测选择/使用阶段。
STAGE_MAP = {'被动关注': '想象', '种草': '想象', '主动评估': '搜索',
             '比价': '搜索', '决定': '搜索', '决定购买': '搜索',
             '购买': '使用', '首次体验': '使用', '持续使用': '使用',
             '完成': '实现', '行为改变': '实现', '新认知': '实现'}
COL_PROFILE, COL_STAGE, COL_EMOTION = 2, 6, 16
COL_P, COL_L, COL_A, COL_ANX_SUB, COL_I, COL_INE_SUB = 17, 18, 19, 20, 21, 22
COL_SCORE, COL_DETAIL = 25, 26
COL_OS, COL_JM, COL_JD, COL_INN, COL_INNTYPE, COL_COMPETE, COL_WTP, COL_FREQ = range(27, 35)
REQUIRED_BASE = {0, 1, 2, 3, 5, 6, 7, 8, 9, 11, 16, 17, 18, 19, 21, 23, 25, 26}
DIMENSIONS = [('完整度', 15), ('精准度', 15), ('颗粒度', 15), ('进步洞察度', 20),
              ('情绪深度', 10), ('四力量清晰度', 10), ('方案价值度', 15)]
DETAIL_PATTERN = ','.join(re.escape(n) + r':([0-9]+)/' + str(cap) for n, cap in DIMENSIONS)


def split_cells(row):
    """仅未转义竖线为边界；连续反斜线按奇偶数判定。保留原转义文字。"""
    row = row.strip()
    boundaries = []
    slashes = 0
    for i, char in enumerate(row):
        if char == '|' and slashes % 2 == 0:
            boundaries.append(i)
        slashes = slashes + 1 if char == '\\' else 0
    if not boundaries or boundaries[0] != 0 or boundaries[-1] != len(row) - 1:
        return []
    return [row[a + 1:b].strip() for a, b in zip(boundaries, boundaries[1:])]


def normalize_header(value):
    value = value.replace('\\|', '|').strip().strip('*').strip()
    # 允许规范表头末尾的枚举注释，不允许任意前缀相似字段蒙混过关。
    value = re.sub(r'[（(][^()（）]*[)）]$', '', value).strip()
    return value


def table_blocks(text):
    """扫描独立Markdown表块；跳过代码围栏中的示例。行号为原文件1-based。"""
    block, fence = [], None
    for number, line in enumerate(text.splitlines(), 1):
        stripped = line.strip()
        marker = re.match(r'^(`{3,}|~{3,})', stripped)
        if fence:
            if re.fullmatch(re.escape(fence[0]) + '{' + str(fence[1]) + ',}\\s*', stripped):
                fence = None
            continue
        if marker:
            if block:
                yield block
                block = []
            fence = (marker[1][0], len(marker[1]))
        elif stripped.startswith('|'):
            block.append((number, line))
        elif block:
            yield block
            block = []
    if block:
        yield block


def _is_scene(header):
    normalized = [normalize_header(h) for h in header]
    return len(header) in (27, 32, 33, 35) or '用户ID' in normalized or '序号' in normalized


def _row_checks(cells, row_num, width, draft, missing):
    errors = []
    def error(message):
        errors.append('行{}: {}'.format(row_num, message))
    required = REQUIRED_BASE | (set(range(27, 35)) if width == 35 else set())
    for index in sorted(required):
        if not cells[index]:
            item = {'line': row_num, 'field': HEADERS[index]}
            missing.append(item)
            if not draft:
                error(HEADERS[index] + '缺失；证据不足请保留为空并使用--draft，不得补造')
    if cells[0] and not re.fullmatch(r'[1-9][0-9]*', cells[0]):
        error('序号必须为正整数')
    if any('同上' in cell for cell in cells):
        error('包含“同上”，每行必须独立可读')
    enums = {4: {'是', '否'}, 6: VALID_STAGES, 11: {'是', '否'},
             20: VALID_ANXIETY_SUB, 22: VALID_INERTIA_SUB}
    if width == 35:
        enums.update({28: VALID_JOB_MAP, 29: VALID_JOB_DIM, 31: VALID_INN_TYPE,
                      32: VALID_COMPETE, 33: VALID_WTP, 34: VALID_FREQ})
    for index, allowed in enums.items():
        if cells[index] and cells[index] not in allowed:
            error('{}值不合法: {}'.format(HEADERS[index], cells[index]))
    for index in [17, 18, 19, 21] + ([30] if width == 35 else []):
        if cells[index] and not re.fullmatch(r'[1-5]', cells[index]):
            error(HEADERS[index] + '必须为1–5整数')
    if cells[11] == '是' and not cells[12]:
        missing.append({'line': row_num, 'field': '补偿行为描述'})
        if not draft:
            error('补偿行为为是但缺少具体描述')
    if cells[11] == '否' and cells[12]:
        error('补偿行为为否时描述须留空，不能靠脚本裁决其中含义')
    if cells[16] and not re.fullmatch(r'[\w\u4e00-\u9fff]+\[[1-5]\](,[\w\u4e00-\u9fff]+\[[1-5]\])?', cells[16]):
        error('情绪须为1–2个标签[1–5]，用英文逗号分隔')
    score = cells[25]
    score_valid = bool(re.fullmatch(r'[0-9]{1,3}', score)) and int(score) <= 100
    if score and not score_valid:
        error('场景总分必须为0–100整数')
    if cells[26]:
        match = re.fullmatch(DETAIL_PATTERN, cells[26])
        if not match:
            error('质量分明细格式不符7维度标准')
        else:
            nums = [int(x) for x in match.groups()]
            for num, (name, cap) in zip(nums, DIMENSIONS):
                if num > cap:
                    error('{}得分{}超过上限{}'.format(name, num, cap))
            if score_valid and sum(nums) != int(score):
                error('明细之和{}不等于总分{}'.format(sum(nums), score))
    if width == 35:
        outcome = cells[27]
        if outcome:
            if not outcome.startswith(OS_VERBS) or len(outcome) < 8 or re.search(r'[A-Za-z]{4,}', outcome):
                error('Outcome Statement须中文方向动词开头、至少8字、无长英文残留；度量项与对象须人工核对')
        strength, kind = cells[30:32]
        if strength in {'1', '2', '3', '4', '5'} and kind in VALID_INN_TYPE:
            if (strength == '1') != (kind == '无'):
                error('创新信号强度1与类型无须互相对应')
    return errors


def validate_row(row, row_num, expected_cols, fix=False, draft=False):
    """兼容旧调用；语义证据仍须人工审核。"""
    cells = split_cells(row)
    if expected_cols not in (27, 35) or len(cells) != expected_cols:
        return ['行{}: 仅支持27/35列且每行须与表头一致'.format(row_num)], row
    fixed = row
    if fix and cells[6] in STAGE_MAP:
        cells[6] = STAGE_MAP[cells[6]]
        fixed = '| ' + ' | '.join(cells) + ' |'
    return _row_checks(cells, row_num, expected_cols, draft, []), fixed


def validate_text(text, draft=False, fix=False):
    errors, warnings, missing, changes = [], [], [], []
    seen, scores = set(), defaultdict(list)
    lines = text.splitlines(keepends=True)
    tables, rows = 0, 0
    for block in table_blocks(text):
        header = split_cells(block[0][1])
        if not _is_scene(header):
            continue
        tables += 1
        width = len(header)
        if width not in (27, 35):
            errors.append('行{}: 表头{}列；只接受27/35列。33列须显式--migrate-33；旧32列需人工映射。'.format(block[0][0], width))
            continue
        normalized = [normalize_header(h) for h in header]
        if normalized != HEADERS[:width]:
            errors.append('行{}: 表头名称或顺序不符标准'.format(block[0][0]))
            continue
        separator = split_cells(block[1][1]) if len(block) > 1 else []
        if len(separator) != width or not all(re.fullmatch(r':?-{3,}:?', x) for x in separator):
            errors.append('行{}: Markdown分隔行无效'.format(block[0][0]))
            continue
        if len(block) < 3:
            errors.append('行{}: 表格没有数据行'.format(block[0][0]))
        for number, row in block[2:]:
            rows += 1
            cells = split_cells(row)
            if len(cells) != width:
                errors.append('行{}: 列数{}不等于{}'.format(number, len(cells), width))
                continue
            if fix and cells[6] in STAGE_MAP:
                before = cells[6]
                cells[6] = STAGE_MAP[before]
                ending = '\r\n' if lines[number - 1].endswith('\r\n') else ('\n' if lines[number - 1].endswith('\n') else '')
                lines[number - 1] = '| ' + ' | '.join(cells) + ' |' + ending
                changes.append({'line': number, 'field': '进步阶段', 'before': before, 'after': cells[6]})
            errors.extend(_row_checks(cells, number, width, draft, missing))
            key = (cells[1], cells[0])
            if all(key):
                if key in seen:
                    errors.append('行{}: 重复复合键 用户ID/序号={}'.format(number, key))
                seen.add(key)
            if re.fullmatch(r'[0-9]{1,3}', cells[25]) and int(cells[25]) <= 100:
                # 按表块和完整用户ID检查，避免跨访谈/跨用户合并配额。
                scores[(tables, cells[1])].append(int(cells[25]))
    if not tables:
        errors.append('未找到有效场景表；代码围栏示例不算交付数据')
    for (table, user), values in scores.items():
        if len(values) >= ANTI_INFLATION_MIN_N:
            for threshold, quota in ((85, .3), (90, .1)):
                count = sum(value >= threshold for value in values)
                if count / len(values) > quota:
                    warnings.append('表{} 用户{}: ≥{}分占{}/{}，超过{}%审校线；回查评分证据，不自动降分。'.format(table, user, threshold, count, len(values), int(quota * 100)))
    status = 'fail' if errors else ('draft_not_deliverable' if draft else 'format_pass_needs_evidence_review')
    report = {'status': status, 'exit_code': 1 if errors else (2 if draft else 0),
              'tables': tables, 'rows': rows, 'errors': errors, 'warnings': warnings,
              'missing': missing, 'changes': changes,
              'limits': ['不证明访谈真实、原话忠实、分类正确、评分有证据或完整覆盖原文',
                         '同用户多次访谈须使用不冲突序号或显式访谈分区；不截断用户ID']}
    return report, ''.join(lines)


def migrate_33(text):
    """只作33→35字段映射；新增类型与竞争留空，禁止用“无”冒充未知。"""
    lines, count = text.splitlines(keepends=True), 0
    for block in table_blocks(text):
        header = split_cells(block[0][1])
        if not _is_scene(header):
            continue
        names = [normalize_header(x) for x in header]
        if len(names) != 33 or len(set(names)) != 33 or set(names) != set(LEGACY_HEADERS):
            raise ValueError('迁移仅接受字段齐全且唯一的33列旧表；32列需人工映射')
        if len(block) < 3:
            raise ValueError('迁移表没有数据行')
        separator = split_cells(block[1][1])
        if len(separator) != 33 or not all(re.fullmatch(r':?-{3,}:?', x) for x in separator):
            raise ValueError('旧表分隔行无效')
        for offset, (number, row) in enumerate(block):
            if offset == 0:
                cells = HEADERS
            elif offset == 1:
                cells = ['---'] * 35
            else:
                values = split_cells(row)
                if len(values) != 33:
                    raise ValueError('行{}: 旧表列数不一致'.format(number))
                record = dict(zip(names, values))
                cells = [record.get(name, '') for name in HEADERS]
            ending = '\n' if lines[number - 1].endswith('\n') else ''
            lines[number - 1] = '| ' + ' | '.join(cells) + ' |' + ending
        count += 1
    if not count:
        raise ValueError('没有可迁移的33列场景表')
    return ''.join(lines)


def validate_file(filepath, fix=False, draft=False, migrate=False):
    path = Path(filepath)
    with path.open(encoding='utf-8', newline='') as handle:
        text = handle.read()
    if migrate:
        text = migrate_33(text)
        draft = True
    report, fixed = validate_text(text, draft=draft, fix=fix)
    if migrate or (fix and report['changes']):
        # 完整重验最终文本；原文件、已存在输出和符号链接均不覆盖。
        checked, _ = validate_text(fixed, draft=draft)
        checked['changes'] = report['changes']
        report = checked
        suffix = '_35_draft.md' if migrate else '_fixed' + (path.suffix or '.md')
        out = path.with_name(path.stem + suffix)
        with out.open('x', encoding='utf-8', newline='') as handle:
            handle.write(fixed)
        report['output'] = str(out)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path')
    parser.add_argument('--draft', action='store_true')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--fix', action='store_true')
    mode.add_argument('--migrate-33', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = validate_file(args.path, args.fix, args.draft, args.migrate_33)
    except (OSError, UnicodeError, ValueError) as exc:
        print('FAIL: {}'.format(exc), file=sys.stderr)
        return 1
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report['exit_code']


if __name__ == '__main__':
    sys.exit(main())

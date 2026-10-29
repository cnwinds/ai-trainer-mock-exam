# -*- coding: utf-8 -*-
"""生成并执行 2026 样卷 B1.2 / B2 参考 notebook，输出到 备考输出/2026/notebooks/（含 HTML）。

python tools/make_y2026_notebooks.py
"""
import pathlib
import nbformat
from nbclient import NotebookClient
from nbconvert import HTMLExporter
from nbformat.v4 import new_notebook, new_code_cell, new_markdown_cell

NB = pathlib.Path(__file__).resolve().parents[2] / "备考输出" / "2026" / "notebooks"

B12 = [
    ("md", "# B1.2 共享会议室预约与空间利用业务场景挖掘（参考答案）\n空白处按官方素材 M1~M4 补全；末尾两格为可视化（任务一要求“使用数据可视化技术展示分析结果”）。"),
    ("code", """import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
bookings = pd.read_csv('meeting_bookings.csv', encoding='utf-8-sig')
rooms = pd.read_csv('meeting_rooms.csv', encoding='utf-8-sig')

# M1（1分）：数据准备
# 按booking_id去重，再排除已取消预约
clean = bookings.drop_duplicates(subset='booking_id').copy()
valid = clean[clean['status'] != '已取消'].copy()

print('数据准备结果')
print('去重后预约数：', len(clean))
print('有效预约数：', len(valid))

# M2（2分）：识别爽约高发时段
# 统计各时段的有效预约数、爽约数和爽约率，并按爽约率降序排列
valid['is_no_show'] = (valid['status'] == '爽约').astype(int)
slot_summary = (valid.groupby('time_slot')
                .agg(有效预约数=('booking_id', 'count'), 爽约数=('is_no_show', 'sum'), 爽约率=('is_no_show', 'mean'))
                .sort_values('爽约率', ascending=False))
slot_summary['爽约率'] = slot_summary['爽约率'].round(3)

print('\\n各时段爽约情况')
print(slot_summary)


# M3（2分）：分析会议室容量匹配
# 只分析已使用预约，关联会议室容量，统计使用场次和平均座位利用率
used = valid[valid['status'] == '已使用'].merge(rooms, on='room_id', how='left')
used['seat_util'] = used["attendees"] / used["capacity"]
room_summary = (used.groupby(['room_id', 'room_name', 'capacity'])
                .agg(使用场次=('booking_id', 'count'), 平均参会人数=('attendees', 'mean'), 平均座位利用率=('seat_util', 'mean'))
                .reset_index().round(3))

print('\\n各会议室空间利用情况')
print(room_summary)


# M4（1分）：输出空间匹配优化候选清单
# 筛选容量不少于12、实际使用不少于20场、平均座位利用率低于40%的会议室
candidates = room_summary[(room_summary['capacity'] >= 12) & (room_summary['使用场次'] >= 20) & (room_summary['平均座位利用率'] < 0.4)]

print('\\n空间匹配优化候选清单')
print(candidates)"""),
    ("code", """# 可视化 1：各时段有效预约数与爽约率
fig, ax1 = plt.subplots(figsize=(7, 4))
s = slot_summary.reindex(['上午', '午间', '下午', '傍晚'])
ax1.bar(s.index, s['有效预约数'], color='#93c5fd', label='有效预约数')
ax1.set_ylabel('有效预约数')
ax2 = ax1.twinx()
ax2.plot(s.index, s['爽约率'], color='#dc2626', marker='o', label='爽约率')
ax2.set_ylabel('爽约率')
for x, v in zip(s.index, s['爽约率']):
    ax2.annotate(f'{v:.1%}', (x, v), textcoords='offset points', xytext=(0, 6), ha='center')
plt.title('各时段有效预约与爽约率')
fig.tight_layout(); plt.show()"""),
    ("code", """# 可视化 2：各会议室容量与平均参会人数、座位利用率
fig, ax = plt.subplots(figsize=(8, 4))
x = room_summary['room_name']
ax.bar(x, room_summary['capacity'], color='#e5e7eb', label='核定座位数')
ax.bar(x, room_summary['平均参会人数'], color='#2563eb', label='平均实际参会人数')
for i, u in enumerate(room_summary['平均座位利用率']):
    ax.text(i, room_summary['capacity'][i] + 0.3, f'{u:.0%}', ha='center')
ax.set_ylabel('人数'); ax.legend(); plt.title('会议室容量匹配（柱顶为平均座位利用率）')
fig.tight_layout(); plt.show()"""),
    ("code", """# 补充：时段 × 会议室爽约率（为“智能提醒/自动释放”找重点对象）
pt = valid.pivot_table(index='room_id', columns='time_slot', values='is_no_show', aggfunc='mean').round(2)
print(pt[['上午', '午间', '下午', '傍晚']])
print('\\n提前预约天数与爽约：')
valid['lead_days'] = (pd.to_datetime(valid['start_time']) - pd.to_datetime(valid['booked_at'])).dt.total_seconds() / 86400
print(valid.groupby(pd.cut(valid['lead_days'], [0, 1, 3, 30]), observed=True)['is_no_show'].agg(['count', 'mean']).round(3))"""),
]

B2 = [
    ("md", "# B2 冷链运输温控异常预警算法测试与数据分析（参考答案）"),
    ("code", """import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix
"""),
    ("code", """# 读取与清洗数据
df = pd.read_csv('cold_chain_shipments.csv')

# 转换发车时间并提取发车小时
df['depart_time'] = pd.to_datetime(df['depart_time'])
df['depart_hour'] = df['depart_time'].dt.hour

# 按运输单号去重，并删除运输时长或传感器缺失率不合法的记录
df = df.drop_duplicates(subset='shipment_id', keep='first')
df = df[(df['planned_hours'] > 0) & (df['sensor_missing_rate'].between(0, 1))]

# 按货物类型的中位数填补 avg_temp 缺失值
df['avg_temp'] = df['avg_temp'].fillna(df.groupby('cargo_type')['avg_temp'].transform('median'))

print('清洗后记录数：', len(df))
"""),
    ("code", """# 统计不同货物类型、不同线路区域的样本数、报警率和平均传感器缺失率
cargo_region_summary = (df.groupby(['cargo_type', 'route_region'])
                        .agg(样本数=('shipment_id', 'count'), 温控报警率=('temp_alarm', 'mean'), 平均传感器缺失率=('sensor_missing_rate', 'mean'))
                        .round(3).reset_index())
print(cargo_region_summary)
"""),
    ("code", """feature_cols = [
    'route_region', 'vehicle_type', 'cargo_type', 'planned_hours',
    'outside_temp', 'avg_temp', 'max_temp', 'door_open_count',
    'sensor_missing_rate', 'driver_experience_years', 'depart_hour'
]
category_cols = ['route_region', 'vehicle_type', 'cargo_type']

# 构造特征矩阵与目标变量，并对分类字段进行独热编码
X = pd.get_dummies(df[feature_cols], columns=category_cols)
y = df['temp_alarm']

# 按 75%/25% 划分训练集和测试集，按 y 分层，random_state=42
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)

# 构建随机森林分类器并完成训练和预测
# 参数：决策树的数量为100，最大深度是6，采用平衡类别权重，random_state=42
model = RandomForestClassifier(n_estimators=100, max_depth=6, class_weight='balanced', random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# 计算精确率、召回率、F1值和混淆矩阵
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
print('precision=', round(precision, 3))
print('recall=', round(recall, 3))
print('f1=', round(f1, 3))
print('confusion matrix=\\n', cm)

# 计算测试集中不同货物类型的召回率
test_result = df.loc[X_test.index, ['shipment_id', 'cargo_type']].copy()
test_result['actual'] = y_test.to_numpy()
test_result['predicted'] = y_pred
cargo_recall = (test_result[test_result['actual'] == 1].groupby('cargo_type')
                .agg(报警样本数=('actual', 'count'), 召回率=('predicted', 'mean')).round(3))
print(cargo_recall)
"""),
    ("code", """# 补充（任务三论据）：分货物类型的漏报数，以及降低阈值对疫苗召回的影响
proba = model.predict_proba(X_test)[:, 1]
test_result['proba'] = proba
for th in (0.5, 0.4, 0.3):
    p = (proba >= th).astype(int)
    print(f'阈值{th}: 总体召回={recall_score(y_test, p):.3f} 精确率={precision_score(y_test, p):.3f}',
          {c: round(g.loc[g.actual == 1, 'proba'].ge(th).mean(), 3) for c, g in test_result.groupby('cargo_type')})
imp = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False).head(8).round(3)
print('\\n特征重要性 Top8\\n', imp)
"""),
]


def build(cells, name):
    nb = new_notebook(cells=[new_markdown_cell(s) if t == "md" else new_code_cell(s) for t, s in cells])
    nb.metadata["kernelspec"] = {"display_name": "Python 3 (ipykernel)", "language": "python", "name": "python3"}
    p = NB / name
    NotebookClient(nb, timeout=300, kernel_name="python3", resources={"metadata": {"path": str(NB)}}).execute()
    nbformat.write(nb, p)
    html, _ = HTMLExporter().from_notebook_node(nb)
    p.with_suffix(".html").write_text(html, encoding="utf-8")
    for c in nb.cells:
        for o in c.get("outputs", []):
            if o.get("text"):
                print(o["text"])


if __name__ == "__main__":
    build(B12, "B1.2_参考.ipynb")
    build(B2, "B2_参考.ipynb")

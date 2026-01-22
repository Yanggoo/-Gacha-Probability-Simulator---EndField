"""
分析工具模块 - 包含统计分析和绘图函数
"""
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端，避免与tkinter冲突
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats
from collections import Counter
from typing import List, Dict
from config import PlayerInfo


def plot_success_failure_pie(success_count: int, failure_count: int, 
                              save_path: str = 'success_failure_pie.png',
                              results: List[Dict] = None):
    """绘制成功和失败的饼图，以及武器配额的累积概率分布
    
    参数:
        success_count: 成功次数
        failure_count: 失败次数
        save_path: 保存路径
        results: 完整的模拟结果列表
    """
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 创建子图布局：1行3列
    fig = plt.figure(figsize=(20, 6))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 1], hspace=0.3, wspace=0.3)
    
    # ========== 左侧：成功率饼图 ==========
    ax1 = fig.add_subplot(gs[0, 0])
    
    # 准备数据
    total = success_count + failure_count
    sizes = [success_count, failure_count]
    labels = [f'成功\n{success_count}次', f'失败\n{failure_count}次']
    percentages = [success_count/total*100, failure_count/total*100]
    colors = ['#66BB6A', '#EF5350']  # 绿色表示成功，红色表示失败
    explode = (0.05, 0.05)  # 突出显示两个部分
    
    # 绘制饼图
    wedges, texts, autotexts = ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                                        autopct='%1.2f%%', startangle=90, 
                                        textprops={'fontsize': 12, 'weight': 'bold'},
                                        pctdistance=0.85)
    
    # 设置百分比文字颜色为白色以便在饼图上清晰显示
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')
    
    # 添加标题
    ax1.set_title('抽卡成功率统计', fontsize=16, fontweight='bold', pad=15)
    
    # 添加图例
    legend_labels = [
        f'成功: {success_count}次 ({percentages[0]:.2f}%)',
        f'失败: {failure_count}次 ({percentages[1]:.2f}%)'
    ]
    ax1.legend(legend_labels, loc='upper left', bbox_to_anchor=(0.7, 1),
               fontsize=10, framealpha=0.9)
    
    # 添加总数文本
    ax1.text(0, -1.3, f'总模拟次数: {total}', 
             ha='center', fontsize=11, weight='bold',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    ax1.axis('equal')  # 保证饼图是圆形
    
    # ========== 中间：剩余武器配额 CDF ==========
    if results:
        ax2 = fig.add_subplot(gs[0, 1])
        remaining_quota = [r.get('剩余配额', 0) for r in results]
        remaining_quota_sorted = np.sort(remaining_quota)
        cdf = np.arange(1, len(remaining_quota_sorted) + 1) / len(remaining_quota_sorted) * 100
        
        ax2.plot(remaining_quota_sorted, cdf, linewidth=2, color='#2196F3')
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.set_xlabel('剩余武器配额', fontsize=12, fontweight='bold')
        ax2.set_ylabel('累积概率 (%)', fontsize=12, fontweight='bold')
        ax2.set_title('剩余武器配额累积分布', fontsize=16, fontweight='bold', pad=15)
        
        # 添加统计信息
        mean_val = np.mean(remaining_quota)
        median_val = np.median(remaining_quota)
        stats_text = f'平均: {mean_val:.1f}\n中位数: {median_val:.1f}'
        ax2.text(0.95, 0.05, stats_text, transform=ax2.transAxes,
                fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # ========== 右侧：额外购买配额 CDF ==========
        ax3 = fig.add_subplot(gs[0, 2])
        extra_quota = [r.get('额外购买配额', 0) for r in results]
        extra_quota_sorted = np.sort(extra_quota)
        cdf2 = np.arange(1, len(extra_quota_sorted) + 1) / len(extra_quota_sorted) * 100
        
        ax3.plot(extra_quota_sorted, cdf2, linewidth=2, color='#FF9800')
        ax3.grid(True, alpha=0.3, linestyle='--')
        ax3.set_xlabel('额外购买配额', fontsize=12, fontweight='bold')
        ax3.set_ylabel('累积概率 (%)', fontsize=12, fontweight='bold')
        ax3.set_title('额外购买配额累积分布', fontsize=16, fontweight='bold', pad=15)
        
        # 添加统计信息
        mean_val2 = np.mean(extra_quota)
        median_val2 = np.median(extra_quota)
        stats_text2 = f'平均: {mean_val2:.1f}\n中位数: {median_val2:.1f}'
        ax3.text(0.95, 0.05, stats_text2, transform=ax3.transAxes,
                fontsize=10, verticalalignment='bottom', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)  # 显式关闭图形，释放资源
    print(f"成功率饼图已保存至: {save_path}")


def plot_combined_distributions(results, success_rate, save_prefix='combined'):
    """绘制综合分布图
    
    参数:
        results: 模拟结果列表
        success_rate: 总体成功率（0-100）
        save_prefix: 保存文件名前缀
    """
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 提取数据
    character_total_no_urgent = [r['角色总抽数（不含紧急）'] for r in results]
    weapon_ten_pulls = [r['武器十连次数'] for r in results]
    success_flags = [r['成功'] for r in results]
    
    # ========== 创建2x2子图布局 ==========
    fig, axes = plt.subplots(2, 2, figsize=(20, 14))
    
    # ========== 左上：角色池累积分布 ==========
    ax1 = axes[0, 0]
    
    # 构建数据：将角色抽数和成功标志配对
    char_data = list(zip(character_total_no_urgent, success_flags))
    char_data.sort(key=lambda x: x[0])  # 按抽数排序
    
    sorted_character = np.array([x[0] for x in char_data])
    cumulative_character = np.arange(1, len(sorted_character) + 1) / len(sorted_character) * 100
    
    # 计算每个点处的实际成功率（在该抽数以下的所有结果中，成功的比例）
    point_success_rates = []
    for i in range(len(sorted_character)):
        success_count_up_to_here = sum(1 for j in range(i+1) if char_data[j][1])
        point_success_rate = success_count_up_to_here / (i + 1) * 100
        point_success_rates.append(point_success_rate)
    
    # 使用matplotlib的LineCollection绘制渐变颜色的线
    from matplotlib.collections import LineCollection
    from matplotlib.patches import Rectangle
    
    # 创建线段
    points = np.array([sorted_character, cumulative_character]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # 为每个线段计算颜色（使用线段起始点的成功率）
    colors = []
    for i in range(len(point_success_rates) - 1):
        rate = point_success_rates[i] / 100  # 归一化到0-1
        # 绿色(0,1,0)到红色(1,0,0)的插值
        r = 1 - rate
        g = rate
        b = 0
        colors.append((r, g, b))
    
    # 创建 LineCollection
    lc = LineCollection(segments, colors=colors, linewidths=2.5)
    ax1.add_collection(lc)
    
    # 自适应x轴范围，留出边距
    x_min = sorted_character.min()
    x_max = sorted_character.max()
    x_range = x_max - x_min
    x_margin = max(x_range * 0.05, 5)  # 至少留5个单位的边距
    ax1.set_xlim(-1, max(10, x_max + x_margin))  # 左边界-1留出空白，右边自适应
    ax1.set_ylim(0, 100)
    
    ax1.set_xlabel('角色池总抽数（不包含紧急寻访）', fontsize=12)
    ax1.set_ylabel('累积概率 (%)', fontsize=12)
    ax1.set_title('角色池累积分布函数（CDF）', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    
    # 添加图例
    legend_elements = [
        Rectangle((0, 0), 1, 1, fc='green', alpha=0.8, label='成功率100%'),
        Rectangle((0, 0), 1, 1, fc='red', alpha=0.8, label='成功率0%'),
        Rectangle((0, 0), 1, 1, fc='yellow', alpha=0.8, label='成功率中间值')
    ]
    ax1.legend(handles=legend_elements, fontsize=10, loc='upper left')
    
    # 设置y轴刻度以10%为单位
    ax1.set_yticks(np.arange(0, 101, 10))
    # 设置x轴刻度，自适应间隔以避免过密
    x_tick_start = 0
    x_tick_end = int(np.ceil(max(10, x_max + x_margin)))
    char_range = x_tick_end - x_tick_start
    # 动态计算刻度间隔，目标是显示10-20个刻度
    char_tick_interval = max(1, int(np.ceil(char_range / 15)))
    # 调整间隔为整数倍（1, 2, 5, 10, 20, 50等）
    nice_intervals = [1, 2, 5, 10, 20, 50, 100]
    char_tick_interval = min([i for i in nice_intervals if i >= char_tick_interval], default=char_tick_interval)
    ax1.set_xticks(np.arange(x_tick_start, x_tick_end + 1, char_tick_interval))
    
    # ========== 右上：武器池累积分布 ==========
    ax2 = axes[0, 1]
    
    # 构建数据：将武器十连次数和成功标志配对
    weapon_data = list(zip(weapon_ten_pulls, success_flags))
    weapon_data.sort(key=lambda x: x[0])  # 按十连次数排序
    
    sorted_weapon = np.array([x[0] for x in weapon_data])
    cumulative_weapon = np.arange(1, len(sorted_weapon) + 1) / len(sorted_weapon) * 100
    
    # 计算每个点处的实际成功率
    point_success_rates_weapon = []
    for i in range(len(sorted_weapon)):
        success_count_up_to_here = sum(1 for j in range(i+1) if weapon_data[j][1])
        point_success_rate = success_count_up_to_here / (i + 1) * 100
        point_success_rates_weapon.append(point_success_rate)
    
    # 创建线段
    points = np.array([sorted_weapon, cumulative_weapon]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    # 为每个线段计算颜色
    colors = []
    for i in range(len(point_success_rates_weapon) - 1):
        rate = point_success_rates_weapon[i] / 100
        r = 1 - rate
        g = rate
        b = 0
        colors.append((r, g, b))
    
    # 创建 LineCollection
    lc = LineCollection(segments, colors=colors, linewidths=2.5)
    ax2.add_collection(lc)
    
    # 自适应x轴范围
    x_min_weapon = sorted_weapon.min()
    x_max_weapon = sorted_weapon.max()
    x_range_weapon = x_max_weapon - x_min_weapon
    x_margin_weapon = max(x_range_weapon * 0.05, 1)  # 至少留1个单位的边距
    ax2.set_xlim(-1, max(10, x_max_weapon + x_margin_weapon))  # 左边界-1留出空白，右边自适应
    ax2.set_ylim(0, 100)
    
    ax2.set_xlabel('武器池十连次数', fontsize=12)
    ax2.set_ylabel('累积概率 (%)', fontsize=12)
    ax2.set_title('武器池累积分布函数（CDF）', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    
    # 添加图例
    ax2.legend(handles=legend_elements, fontsize=10, loc='upper left')
    ax2.set_yticks(np.arange(0, 101, 10))
    
    # 设置x轴刻度，自适应间隔以避免过密
    x_tick_start_weapon = 0
    x_tick_end_weapon = int(np.ceil(max(10, x_max_weapon + x_margin_weapon)))
    weapon_range = x_tick_end_weapon - x_tick_start_weapon
    # 动态计算刻度间隔，目标是显示10-20个刻度
    weapon_tick_interval = max(1, int(np.ceil(weapon_range / 15)))
    # 调整间隔为整数倍（1, 2, 5, 10, 20, 50等）
    weapon_tick_interval = min([i for i in nice_intervals if i >= weapon_tick_interval], default=weapon_tick_interval)
    ax2.set_xticks(np.arange(x_tick_start_weapon, x_tick_end_weapon + 1, weapon_tick_interval))
    
    # ========== 左下：角色池成功/失败堆叠柱状图 ==========
    ax3 = axes[1, 0]
    
    # 统计每个抽数对应的成功和失败数量
    from collections import Counter
    char_counter = Counter(character_total_no_urgent)
    unique_char_pulls = sorted(char_counter.keys())
    
    # 为每个抽数统计成功和失败的数量
    char_success_counts = []
    char_failure_counts = []
    
    for pull_count in unique_char_pulls:
        success_count = sum(1 for char_pull, success in zip(character_total_no_urgent, success_flags) 
                          if char_pull == pull_count and success)
        failure_count = sum(1 for char_pull, success in zip(character_total_no_urgent, success_flags) 
                          if char_pull == pull_count and not success)
        char_success_counts.append(success_count)
        char_failure_counts.append(failure_count)
    
    # 计算每个位置的成功率，并用固定高度的柱子表示
    bar_height_max = 200  # 固定的柱子最大高度（对应200%）
    char_success_heights = []
    char_failure_heights = []
    
    for success_count, failure_count in zip(char_success_counts, char_failure_counts):
        total = success_count + failure_count
        if total > 0:
            success_rate = success_count / total
        else:
            success_rate = 0
        char_success_heights.append(bar_height_max * 1/2 * success_rate)
        char_failure_heights.append(bar_height_max * 1/2 * (1 - success_rate))
    
    # 采样以避免柱状图过于密集
    n_bars = min(50, len(unique_char_pulls))  # 最多50个柱子
    if len(unique_char_pulls) > n_bars:
        bar_indices = np.linspace(0, len(unique_char_pulls) - 1, n_bars, dtype=int)
        sampled_pulls = [unique_char_pulls[i] for i in bar_indices]
        sampled_success = [char_success_heights[i] for i in bar_indices]
        sampled_failure = [char_failure_heights[i] for i in bar_indices]
    else:
        sampled_pulls = unique_char_pulls
        sampled_success = char_success_heights
        sampled_failure = char_failure_heights
    
    # 绘制堆叠柱状图
    bar_width = max(x_range / n_bars * 0.8, 0.5)
    
    # 绘制成功部分（绿色，底部）
    ax3.bar(sampled_pulls, sampled_success, width=bar_width, 
           color='green', alpha=0.7, label='成功', edgecolor='black', linewidth=0.5)
    
    # 绘制失败部分（红色，上部）
    ax3.bar(sampled_pulls, sampled_failure, width=bar_width, bottom=sampled_success,
           color='red', alpha=0.7, label='失败', edgecolor='black', linewidth=0.5)
    
    ax3.set_xlim(-1, max(10, x_max + x_margin))  # 左边界-1留出空白，右边自适应
    ax3.set_xlabel('角色池总抽数（不包含紧急寻访）', fontsize=12)
    ax3.set_ylabel('成功率 (%)', fontsize=12)
    ax3.set_title('角色池成功/失败分布（堆叠柱状图）', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    ax3.legend(fontsize=10, loc='upper right')
    ax3.set_xticks(np.arange(x_tick_start, x_tick_end + 1, char_tick_interval))
    ax3.set_ylim(0, bar_height_max)
    
    # ========== 右下：武器池成功/失败堆叠柱状图 ==========
    ax4 = axes[1, 1]
    
    # 统计每个十连次数对应的成功和失败数量
    weapon_counter = Counter(weapon_ten_pulls)
    unique_weapon_pulls = sorted(weapon_counter.keys())
    
    weapon_success_counts = []
    weapon_failure_counts = []
    
    for pull_count in unique_weapon_pulls:
        success_count = sum(1 for weapon_pull, success in zip(weapon_ten_pulls, success_flags) 
                          if weapon_pull == pull_count and success)
        failure_count = sum(1 for weapon_pull, success in zip(weapon_ten_pulls, success_flags) 
                          if weapon_pull == pull_count and not success)
        weapon_success_counts.append(success_count)
        weapon_failure_counts.append(failure_count)
    
    # 计算每个位置的成功率，并用固定高度的柱子表示
    weapon_success_heights = []
    weapon_failure_heights = []
    
    for success_count, failure_count in zip(weapon_success_counts, weapon_failure_counts):
        total = success_count + failure_count
        if total > 0:
            success_rate = success_count / total
        else:
            success_rate = 0
        weapon_success_heights.append(bar_height_max * 1/2 * success_rate)
        weapon_failure_heights.append(bar_height_max * 1/2 * (1 - success_rate))
    
    # 采样以避免柱状图过于密集
    n_bars_weapon = min(50, len(unique_weapon_pulls))  # 最多50个柱子
    if len(unique_weapon_pulls) > n_bars_weapon:
        bar_indices_weapon = np.linspace(0, len(unique_weapon_pulls) - 1, n_bars_weapon, dtype=int)
        sampled_weapon_pulls = [unique_weapon_pulls[i] for i in bar_indices_weapon]
        sampled_weapon_success = [weapon_success_heights[i] for i in bar_indices_weapon]
        sampled_weapon_failure = [weapon_failure_heights[i] for i in bar_indices_weapon]
    else:
        sampled_weapon_pulls = unique_weapon_pulls
        sampled_weapon_success = weapon_success_heights
        sampled_weapon_failure = weapon_failure_heights
    
    # 绘制堆叠柱状图
    bar_width_weapon = max(x_range_weapon / n_bars_weapon * 0.8, 0.5)
    
    # 绘制成功部分（绿色，底部）
    ax4.bar(sampled_weapon_pulls, sampled_weapon_success, width=bar_width_weapon, 
           color='green', alpha=0.7, label='成功', edgecolor='black', linewidth=0.5)
    
    # 绘制失败部分（红色，上部）
    ax4.bar(sampled_weapon_pulls, sampled_weapon_failure, width=bar_width_weapon, bottom=sampled_weapon_success,
           color='red', alpha=0.7, label='失败', edgecolor='black', linewidth=0.5)
    
    ax4.set_xlim(-1, max(10, x_max_weapon + x_margin_weapon))  # 左边界-1留出空白，右边自适应
    ax4.set_xlabel('武器池十连次数', fontsize=12)
    ax4.set_ylabel('成功率 (%)', fontsize=12)
    ax4.set_title('武器池成功/失败分布（堆叠柱状图）', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')
    ax4.legend(fontsize=10, loc='upper right')
    ax4.set_ylim(0, bar_height_max)
    ax4.set_xticks(np.arange(x_tick_start_weapon, x_tick_end_weapon + 1, weapon_tick_interval))
    
    plt.tight_layout()
    plt.savefig(f'{save_prefix}_cdf.png', dpi=300, bbox_inches='tight')
    plt.close()  # 显式关闭图形，释放资源
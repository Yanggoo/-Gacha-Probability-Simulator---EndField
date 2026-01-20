import random
import numpy as np
import matplotlib.pyplot as plt
from collections import Counter
from typing import List, Dict, Tuple


# ==================== 全局配置参数 ====================
# 玩家信息
SOFT_PITY_ACCUMULATE = 0  # 小保底当前累计抽数
TOTAL_PULLS_USED = 0  # 当前卡池开启后已经使用的抽数
TEN_PULLS_AVAILABLE = 0  # 当前可用的免费十连数(不考虑加急招募)
URGENT_RECRUITMENT_USED = False  # 是否已经使用加急招募
URGENT_RECRUITMENT_ENABLED = True  # 是否启用加急招募功能
LIMITED_OBTAINED = False  # 是否已经获得限定干员
INITIAL_WEAPON_QUOTA = 0  # 初始武器配额
GOALS = {  # 玩家抽卡目标
    "限定": 1  # 目标：1个限定
}
ALWAYS_PULL_TEN = False  # 是否总是进行十连抽
GOT_FIVE_OR_SIX_STAR_IN_10_PULLS = False  # 最近十抽是否至少获得过一个5星或6星

# 卡池规则信息

# 角色稀有度概率配置
FOUR_STAR_PROBABILITY = 0.50   # 4星概率 50%
FIVE_STAR_PROBABILITY = 0.492   # 5星概率 49.2%
BASE_SIX_PROBABILITY = 8.0 / 1000.0  # 基础六星概率 0.8%
SOFT_PITY = 80  # 小保底触发点：抽一个六星
HARD_PITY = 120  # 大保底触发点：抽当期UP六星
LOOP_PITY = 240  # 循环保底触发点：直接给一个当期UP六星
URGENT_RECRUITMENT_PITY = 30  # 加急招募赠送触发点：给一个免费十连（与保底数互不影响）

# 六星干员池
SIX_STAR_POOL = {
    "限定": 1.0 / 2.0,  # 50%概率
    "伊冯": 1.0 / 14.0,  # 7.14%概率
    "洁哥": 1.0 / 14.0,  # 7.14%概率
    "别礼": 1.0 / 14.0,  # 7.14%概率
    "骏卫": 1.0 / 14.0,  # 7.14%概率
    "黎风": 1.0 / 14.0,  # 7.14%概率
    "小羊": 1.0 / 14.0,  # 7.14%概率
    "余烬": 1.0 / 14.0  # 7.14%概率
}

# 概率提升机制配置 (小保底累计抽数区间及对应的概率增加值)
# 格式: (起始抽数, 结束抽数, 概率增加值)
PROBABILITY_BOOST_RANGES = [
    (65, 70, 0.04),  # 65-70抽: 提升4%
    (71, 75, 0.08),  # 71-75抽: 提升8%
    (76, 79, 0.10),  # 76-79抽: 提升10%
]

# 武器配额配置 - 根据稀有度获得的武器配额数量
WEAPON_QUOTA_PER_RARITY = {
    4: 1,   # 4星角色给1个武器配额
    5: 5,   # 5星角色给5个武器配额
    6: 10   # 6星角色给10个武器配额
}

# 模拟信息
SIMULATION_RUNS = 10000  # 模拟次数
# ====================================================


def goals_achieved(goals_achieved_dict: Dict[str, int], goals: Dict[str, int]) -> bool:
    """检查是否达成目标"""
    for goal, count in goals.items():
        if goals_achieved_dict.get(goal, 0) < count:
            return False
    return True


def get_six_star_by_probability() -> str:
    """根据概率获取一个六星干员"""
    rand_value = random.random()
    cumulative_probability = 0.0
    for character, probability in SIX_STAR_POOL.items():
        cumulative_probability += probability
        if rand_value <= cumulative_probability:
            return character
    return list(SIX_STAR_POOL.keys())[-1]  # 返回最后一个


def get_current_six_star_probability(base_probability: float, soft_pity_count: int) -> float:
    """根据当前小保底累计抽数计算六星概率
    
    参数:
        base_probability: 基础六星概率
        soft_pity_count: 当前小保底累计抽数
    
    返回:
        当前的六星概率
    """
    # 遍历概率提升区间配置
    for start, end, boost in PROBABILITY_BOOST_RANGES:
        if start <= soft_pity_count <= end:
            return base_probability + boost
    
    # 不在任何特殊区间内，返回基础概率
    return base_probability


def get_character_by_probability(current_probability: float = None) -> Tuple[str, int]:
    """根据概率获取一个干员
    
    参数:
        current_probability: 当前六星概率，如果为None则使用基础概率
    
    返回:
        (角色名称, 稀有度) - 角色名称为""表示未抽中六星，稀有度为4/5/6
    """
    if current_probability is None:
        current_probability = BASE_SIX_PROBABILITY
    rand_value = random.random()
    
    # 检查是否抽中六星
    if rand_value <= current_probability:
        return get_six_star_by_probability(), 6
    
    # 未抽中六星，判断是4星还是5星
    # 剩余概率 = 1 - 六星概率
    remaining_prob = 1.0 - current_probability
    # 在剩余概率中，4星和5星的占比
    four_star_in_remaining = FOUR_STAR_PROBABILITY / (FOUR_STAR_PROBABILITY + FIVE_STAR_PROBABILITY)
    
    # 在非六星中随机判断
    rand_value_2 = random.random()
    if rand_value_2 <= four_star_in_remaining:
        return "", 4  # 4星角色
    else:
        return "", 5  # 5星角色


def perform_single_pull(soft_pity_accumulate: int, total_pulls: int, 
                       limited_obtained: bool, obtained_six_stars: List[str],
                       weapon_quota: int = 0) -> tuple:
    """执行单次抽卡
    
    返回:
        (soft_pity_accumulate, total_pulls, limited_obtained, weapon_quota)
    """
    soft_pity_accumulate += 1
    total_pulls += 1
    
    # 检查循环保底，这个是赠送，还要继续抽
    if total_pulls >= LOOP_PITY and total_pulls % LOOP_PITY == 0:
        # 直接获得一个当期UP六星
        obtained_six_stars.append("限定")
        weapon_quota += WEAPON_QUOTA_PER_RARITY[6]
    
    # 检查大保底
    if not limited_obtained and total_pulls == HARD_PITY:
        # 获得一个当期UP六星
        obtained_six_stars.append("限定")
        weapon_quota += WEAPON_QUOTA_PER_RARITY[6]
        limited_obtained = True
        # 这里存疑，大保底出金是否重置小保底？先假设重置
        soft_pity_accumulate = 0  # 出金后重置小保底
    # 检查小保底
    elif not limited_obtained and soft_pity_accumulate == SOFT_PITY:
        # 抽一个六星
        six_star = get_six_star_by_probability()
        obtained_six_stars.append(six_star)
        weapon_quota += WEAPON_QUOTA_PER_RARITY[6]
        if six_star == "限定":
            limited_obtained = True
        soft_pity_accumulate = 0  # 出金后重置小保底
    else:
        # 正常抽卡，使用区间概率提升机制
        current_probability = get_current_six_star_probability(BASE_SIX_PROBABILITY, soft_pity_accumulate)
        character, rarity = get_character_by_probability(current_probability)
        weapon_quota += WEAPON_QUOTA_PER_RARITY[rarity]
        if character == "限定":
            limited_obtained = True
        if character != "":
            obtained_six_stars.append(character)
            soft_pity_accumulate = 0  # 出金后重置小保底
    
    return soft_pity_accumulate, total_pulls, limited_obtained, weapon_quota


def perform_ten_pulls(soft_pity_accumulate: int, total_pulls: int, 
                     ten_pull_count: int, ten_pull_count_urgent: int,
                     limited_obtained: bool, weapon_quota: int = 0) -> tuple:
    """执行一次十连抽
    
    返回:
        (soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, 
         limited_obtained, obtained_six_stars, weapon_quota)
    """
    obtained_six_stars = []
    
    # 有紧急招募且未使用，则优先使用，不需要更新小保底累计
    use_urgent_pulls = ten_pull_count_urgent != 0
    
    for i in range(10):
        # 非紧急招募十连，检查大保底和循环保底
        if not use_urgent_pulls:
            soft_pity_accumulate, total_pulls, limited_obtained, weapon_quota = perform_single_pull(
                soft_pity_accumulate, total_pulls, limited_obtained, obtained_six_stars, weapon_quota
            )
        else:
            # 紧急招募使用基础概率（不累计大小保底）
            # 这里也存疑，紧急寻访吃不吃概率提升机制？先认为不吃
            current_probability = BASE_SIX_PROBABILITY
            character, rarity = get_character_by_probability(current_probability)
            
            weapon_quota += WEAPON_QUOTA_PER_RARITY[rarity]
            if character != "":
                obtained_six_stars.append(character)
    
    if use_urgent_pulls:
        ten_pull_count_urgent -= 1
    elif ten_pull_count > 0:
        ten_pull_count -= 1
    
    return soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, limited_obtained, obtained_six_stars, weapon_quota


def update_goals_achieved(goals_achieved_dict: Dict[str, int], obtained_six_stars: List[str]):
    """更新已达成目标"""
    for star in obtained_six_stars:
        goals_achieved_dict[star] = goals_achieved_dict.get(star, 0) + 1


def single_simulation() -> Dict[str, int]:
    """执行单次完整模拟，返回使用的各类抽数和武器配额"""
    # 初始化runtime信息
    goals_achieved_dict = {}
    limited_obtained = LIMITED_OBTAINED
    ten_pull_count = TEN_PULLS_AVAILABLE
    ten_pull_count_urgent = 1 if (URGENT_RECRUITMENT_ENABLED and TOTAL_PULLS_USED >= URGENT_RECRUITMENT_PITY and not URGENT_RECRUITMENT_USED) else 0
    urgent_recruitment_got = ten_pull_count_urgent > 0
    total_pulls = TOTAL_PULLS_USED
    soft_pity_accumulate = SOFT_PITY_ACCUMULATE
    
    # 记录三种抽数
    pulls_used = 0  # 兑换抽数（玩家付费）
    free_ten_pulls_used = 0  # 免费十连寻访凭证使用数
    urgent_pulls_used = 0  # 紧急招募十连使用数
    
    # 记录武器配额（从初始配额开始）
    weapon_quota = INITIAL_WEAPON_QUOTA
    
    # 记录初始的免费十连数量
    initial_ten_pull_count = TEN_PULLS_AVAILABLE
    
    while not goals_achieved(goals_achieved_dict, GOALS):
        # 紧急招募更新（仅当启用时）
        if URGENT_RECRUITMENT_ENABLED and not urgent_recruitment_got and total_pulls >= URGENT_RECRUITMENT_PITY:
            ten_pull_count_urgent += 1
            urgent_recruitment_got = True
        
        # 是否有十连寻访凭证
        has_ten_pull = ten_pull_count > 0 or ten_pull_count_urgent > 0
        
        if has_ten_pull:
            # 记录使用哪种十连
            using_urgent = ten_pull_count_urgent > 0
            
            soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, limited_obtained, obtained_six_stars, weapon_quota = perform_ten_pulls(
                soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, limited_obtained, weapon_quota
            )
            update_goals_achieved(goals_achieved_dict, obtained_six_stars)
            
            # 统计使用的十连类型
            if using_urgent:
                urgent_pulls_used += 10
            else:
                free_ten_pulls_used += 10
        else:
            # 总是十连抽
            if ALWAYS_PULL_TEN:
                soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, limited_obtained, obtained_six_stars, weapon_quota = perform_ten_pulls(
                    soft_pity_accumulate, total_pulls, ten_pull_count, ten_pull_count_urgent, limited_obtained, weapon_quota
                )
                update_goals_achieved(goals_achieved_dict, obtained_six_stars)
                pulls_used += 10
            else:
                # 单抽
                obtained_six_stars = []
                soft_pity_accumulate, total_pulls, limited_obtained, weapon_quota = perform_single_pull(
                    soft_pity_accumulate, total_pulls, limited_obtained, obtained_six_stars, weapon_quota
                )
                update_goals_achieved(goals_achieved_dict, obtained_six_stars)
                pulls_used += 1
    
    return {
        '兑换抽数': pulls_used,
        '免费十连': free_ten_pulls_used,
        '紧急招募': urgent_pulls_used,
        '总抽数': pulls_used + free_ten_pulls_used + urgent_pulls_used,
        '武器配额': weapon_quota
    }


def analyze_results(results: List[int]) -> Dict:
    """分析模拟结果"""
    results_array = np.array(results)
    
    analysis = {
        '平均抽数': np.mean(results_array),
        '中位数': np.median(results_array),
        '标准差': np.std(results_array),
        '最小抽数': np.min(results_array),
        '最大抽数': np.max(results_array),
        '25分位数': np.percentile(results_array, 25),
        '75分位数': np.percentile(results_array, 75),
        '90分位数': np.percentile(results_array, 90),
        '95分位数': np.percentile(results_array, 95),
        '99分位数': np.percentile(results_array, 99),
    }
    
    return analysis


def plot_distribution(results_paid: List[int], results_free: List[int], 
                      results_urgent: List[int], results_total: List[int], 
                      save_path: str = 'gacha_distribution.png'):
    """绘制总抽数分布图
    
    参数:
        results_paid: 兑换抽数列表
        results_free: 免费十连抽数列表
        results_urgent: 紧急招募抽数列表
        results_total: 总抽数列表
        save_path: 保存路径
    """
    plt.figure(figsize=(18, 10))
    
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    # 子图1: 直方图（只显示兑换抽数）- 左上
    plt.subplot(2, 2, 1)
    bins = 50
    plt.hist(results_paid, bins=bins, 
             color='#FF6B6B',
             alpha=0.7, edgecolor='black')
    plt.xlabel('兑换抽数')
    plt.ylabel('频次')
    plt.title('直方图')
    plt.grid(True, alpha=0.3)
    
    # 子图2: 概率密度估计（只用兑换抽数）- 右上
    plt.subplot(2, 2, 2)
    try:
        from scipy import stats
        density = stats.gaussian_kde(results_paid)
        xs = np.linspace(min(results_paid), max(results_paid), 200)
        plt.plot(xs, density(xs), linewidth=2, color='green')
        plt.fill_between(xs, density(xs), alpha=0.3, color='green')
        plt.xlabel('兑换抽数')
        plt.ylabel('概率密度')
        plt.title('概率密度估计 (KDE)')
        plt.grid(True, alpha=0.3)
    except ImportError:
        plt.text(0.5, 0.5, '需要安装 scipy\npip install scipy', 
                ha='center', va='center', fontsize=12)
        plt.title('概率密度估计 (需要scipy)')
    
    # 子图3: 累积分布函数（只用兑换抽数）- 下方横跨两列
    plt.subplot(2, 1, 2)
    sorted_results = np.sort(results_paid)
    cumulative = np.arange(1, len(sorted_results) + 1) / len(sorted_results) * 100
    plt.plot(sorted_results, cumulative, linewidth=2, color='coral')
    plt.xlabel('兑换抽数')
    plt.ylabel('累积概率 (%)')
    plt.title('累积分布函数 (CDF)')
    plt.grid(True, alpha=0.3)
    
    # 找到累积概率突然增长的点
    # 当(x-1,x)的增长 > 3倍的相邻区间增长时，在x-1和x处画线
    if len(cumulative) > 2:
        prob_diffs = np.diff(cumulative)
        marked_y_values = set()
        
        for i in range(1, len(prob_diffs) - 1):
            current_growth = prob_diffs[i]  # (x-1, x)的增长
            prev_growth = prob_diffs[i-1]    # (x-2, x-1)的增长
            next_growth = prob_diffs[i+1]    # (x, x+1)的增长
            
            # 检查当前增长是否是前后增长的3倍以上
            if current_growth > 3 * prev_growth or current_growth > 3 * next_growth:
                # 在x-1处画线
                y_val_before = cumulative[i]
                if y_val_before not in marked_y_values:
                    marked_y_values.add(y_val_before)
                    plt.axhline(y=y_val_before, color='green', linestyle=':', alpha=0.6, linewidth=1.5)
                    plt.text(min(results_paid), y_val_before, f'{y_val_before:.1f}%', 
                            va='bottom', ha='left', fontsize=9, color='green')
                
                # 在x处画线
                y_val_after = cumulative[i+1]
                if y_val_after not in marked_y_values:
                    marked_y_values.add(y_val_after)
                    plt.axhline(y=y_val_after, color='green', linestyle=':', alpha=0.6, linewidth=1.5)
                    plt.text(min(results_paid), y_val_after, f'{y_val_after:.1f}%', 
                            va='bottom', ha='left', fontsize=9, color='green')
    
    # 设置x轴刻度以5为单位
    x_min = int(min(results_paid) / 5) * 5
    x_max = int(max(results_paid) / 5) * 5 + 5
    plt.xticks(np.arange(x_min, x_max + 1, 5))
    # 设置y轴刻度以10%为单位
    plt.yticks(np.arange(0, 101, 10))
    plt.legend()
    
    plt.tight_layout()
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"图表已保存至: {save_path}")
    plt.show()


def plot_pulls_breakdown(paid_pulls: List[int], free_pulls: List[int], 
                         urgent_pulls: List[int], save_path: str = 'pulls_breakdown.png'):
    """绘制三种抽数的对比图"""
    plt.figure(figsize=(12, 8))
    
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False
    
    colors = ['#FF6B6B', '#4ECDC4', '#95E1D3']
    
    # 子图1: 兑换抽数分布
    plt.subplot(2, 2, 1)
    bins = 50
    plt.hist(paid_pulls, bins=bins, alpha=0.7, color='#FF6B6B', 
             edgecolor='black', label='兑换抽数')
    plt.xlabel('抽数')
    plt.ylabel('频次')
    plt.title('兑换抽数分布')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图2: 免费十连分布
    plt.subplot(2, 2, 2)
    plt.hist(free_pulls, bins=30, alpha=0.7, color='#4ECDC4', 
             edgecolor='black', label='免费十连')
    plt.xlabel('抽数')
    plt.ylabel('频次')
    plt.title('免费十连分布')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图3: 紧急招募分布
    plt.subplot(2, 2, 3)
    plt.hist(urgent_pulls, bins=30, alpha=0.7, color='#95E1D3', 
             edgecolor='black', label='紧急招募')
    plt.xlabel('抽数')
    plt.ylabel('频次')
    plt.title('紧急招募抽数分布')
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # 子图4: 平均值柱状图
    plt.subplot(2, 2, 4)
    categories = ['兑换抽数', '免费十连', '紧急招募']
    means = [np.mean(paid_pulls), np.mean(free_pulls), np.mean(urgent_pulls)]
    bars = plt.bar(categories, means, color=colors, alpha=0.7, edgecolor='black')
    plt.ylabel('平均抽数')
    plt.title('各类抽数平均值')
    plt.grid(True, alpha=0.3, axis='y')
    
    # 在柱子上标注数值
    for bar, mean in zip(bars, means):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{mean:.1f}',
                ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    print(f"抽数分解图已保存至: {save_path}")
    plt.show()


def main():
    """主函数"""
    print("="*60)
    print("明日方舟·终末地 抽卡概率模拟器")
    print("="*60)
    
    # 显示配置
    print("\n当前配置:")
    print("-"*60)
    print(f"基础六星概率: {BASE_SIX_PROBABILITY*100}%")
    print(f"小保底: {SOFT_PITY}抽 (必出六星)")
    print(f"大保底: {HARD_PITY}抽 (必出限定UP)")
    print(f"循环保底: {LOOP_PITY}抽 (额外送限定UP)")
    print(f"加急招募: {URGENT_RECRUITMENT_PITY}抽 (送免费十连，不计入保底) - {'已启用' if URGENT_RECRUITMENT_ENABLED else '已禁用'}")
    print(f"\n玩家初始状态:")
    print(f"  小保底累计: {SOFT_PITY_ACCUMULATE} 抽")
    print(f"  总抽数: {TOTAL_PULLS_USED} 抽")
    print(f"  免费十连: {TEN_PULLS_AVAILABLE} 个")
    print(f"  加急招募已用: {'是' if URGENT_RECRUITMENT_USED else '否'}")
    print(f"  已获得限定: {'是' if LIMITED_OBTAINED else '否'}")
    print(f"  初始武器配额: {INITIAL_WEAPON_QUOTA}")
    print(f"\n六星干员池:")
    for char, prob in SIX_STAR_POOL.items():
        marker = " ← 限定UP" if char == "限定" else ""
        print(f"  {char}: {prob*100:.2f}%{marker}")
    print(f"\n抽卡目标:")
    for goal, count in GOALS.items():
        print(f"  {goal}: {count} 个")
    print(f"\n模拟次数: {SIMULATION_RUNS}")
    print(f"抽卡模式: {'总是十连' if ALWAYS_PULL_TEN else '单抽'}")
    print("="*60)
    
    # 运行模拟
    print(f"\n开始运行 {SIMULATION_RUNS} 次模拟...")
    results_paid = []
    results_free = []
    results_urgent = []
    results_total = []
    results_weapon_quota = []
    
    for i in range(SIMULATION_RUNS):
        result = single_simulation()
        results_paid.append(result['兑换抽数'])
        results_free.append(result['免费十连'])
        results_urgent.append(result['紧急招募'])
        results_total.append(result['总抽数'])
        results_weapon_quota.append(result['武器配额'])
        
        if (i + 1) % 1000 == 0:
            print(f"已完成 {i + 1}/{SIMULATION_RUNS} 次模拟")
    
    # 分析总抽数结果
    analysis = analyze_results(results_total)
    
    # 打印统计信息
    print("\n" + "="*60)
    print("模拟结果统计 (总抽数)")
    print("="*60)
    for key, value in analysis.items():
        print(f"{key:>12}: {value:>8.2f} 抽")
    
    # 打印各类抽数的统计
    print("\n" + "="*60)
    print("各类抽数统计")
    print("="*60)
    print(f"{'类型':>12} | {'平均值':>10} | {'中位数':>10} | {'标准差':>10}")
    print("-"*60)
    print(f"{'兑换抽数':>12} | {np.mean(results_paid):>10.2f} | {np.median(results_paid):>10.2f} | {np.std(results_paid):>10.2f}")
    print(f"{'免费十连':>12} | {np.mean(results_free):>10.2f} | {np.median(results_free):>10.2f} | {np.std(results_free):>10.2f}")
    print(f"{'紧急招募':>12} | {np.mean(results_urgent):>10.2f} | {np.median(results_urgent):>10.2f} | {np.std(results_urgent):>10.2f}")
    print(f"{'总抽数':>12} | {np.mean(results_total):>10.2f} | {np.median(results_total):>10.2f} | {np.std(results_total):>10.2f}")
    
    # 打印武器配额统计
    print("\n" + "="*60)
    print("武器配额统计")
    print("="*60)
    print(f"配置: 4星={WEAPON_QUOTA_PER_RARITY[4]}配额, 5星={WEAPON_QUOTA_PER_RARITY[5]}配额, 6星={WEAPON_QUOTA_PER_RARITY[6]}配额")
    print(f"初始武器配额: {INITIAL_WEAPON_QUOTA}")
    print("-"*60)
    # 计算新增配额（累计配额 - 初始配额）
    results_new_quota = [quota - INITIAL_WEAPON_QUOTA for quota in results_weapon_quota]
    print(f"平均新增配额: {np.mean(results_new_quota):.2f}")
    print(f"平均累计配额: {np.mean(results_weapon_quota):.2f} (初始{INITIAL_WEAPON_QUOTA} + 新增{np.mean(results_new_quota):.2f})")
    print(f"\n累计配额分布:")
    print(f"  中位数: {np.median(results_weapon_quota):.2f}")
    print(f"  标准差: {np.std(results_weapon_quota):.2f}")
    print(f"  最小值: {np.min(results_weapon_quota):.2f}")
    print(f"  最大值: {np.max(results_weapon_quota):.2f}")
    print(f"  25分位数: {np.percentile(results_weapon_quota, 25):.2f}")
    print(f"  75分位数: {np.percentile(results_weapon_quota, 75):.2f}")
    print(f"  90分位数: {np.percentile(results_weapon_quota, 90):.2f}")
    
    # 计算平均节省
    avg_saved = np.mean(results_free) + np.mean(results_urgent)
    print(f"\n平均节省抽数: {avg_saved:.2f} 抽 (免费十连 + 紧急招募)")
    print(f"平均实际兑换: {np.mean(results_paid):.2f} 抽")
    
    # 打印分布详情
    counter = Counter(results_paid)
    print("\n最常见的兑换抽数 (Top 10):")
    for pulls, count in counter.most_common(10):
        percentage = count / SIMULATION_RUNS * 100
        print(f"  {pulls:>3} 抽: {count:>6} 次 ({percentage:>5.2f}%)")
    
    # 计算概率区间
    print("\n概率区间 (总抽数):")
    percentiles = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]
    for p in percentiles:
        value = np.percentile(results_total, p)
        print(f"  {p:>2}% 的玩家在 {value:.0f} 抽内达成目标")
    
    print("="*60)
    
    # 绘制总抽数分布图
    print("\n正在生成总抽数分布图...")
    plot_distribution(results_paid, results_free, results_urgent, results_total, 
                     save_path='gacha_total_distribution.png')
    
    # 绘制抽数分解对比图
    print("\n正在生成抽数分解对比图...")
    plot_pulls_breakdown(results_paid, results_free, results_urgent, save_path='pulls_breakdown.png')
    
    print("\n模拟完成！")


if __name__ == "__main__":
    main()

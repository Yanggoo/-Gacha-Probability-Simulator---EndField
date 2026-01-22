"""
角色池抽卡工具模块 - 包含角色池抽卡相关的核心逻辑函数
"""
import random
from typing import List, Dict, Tuple
from config import CharacterPoolConfig, PlayerInfo, CharacterRuntimeInfo


def character_goals_achieved(goals_achieved_dict: Dict[str, int], goals: Dict[str, int]) -> bool:
    """检查角色池是否达成目标
    
    参数:
        goals_achieved_dict: 已达成的目标字典
        goals: 目标字典
    
    返回:
        是否达成所有目标
    """
    for goal, count in goals.items():
        if goals_achieved_dict.get(goal, 0) < count:
            return False
    return True


def get_six_star_character_by_probability(pool_config: CharacterPoolConfig) -> str:
    """根据概率获取一个六星角色
    
    参数:
        pool_config: 角色池配置
    
    返回:
        六星角色名称
    """
    rand_value = random.random()
    cumulative_probability = 0.0
    for character, probability in pool_config.six_star_pool.items():
        cumulative_probability += probability
        if rand_value <= cumulative_probability:
            return character
    return list(pool_config.six_star_pool.keys())[-1]


def get_current_six_star_character_probability(pool_config: CharacterPoolConfig, soft_pity_count: int) -> float:
    """根据当前小保底累计抽数计算六星角色概率
    
    参数:
        pool_config: 角色池配置
        soft_pity_count: 当前小保底累计抽数
    
    返回:
        当前的六星角色概率
    """
    # 遍历概率提升区间配置
    for start, end, boost in pool_config.probability_boost_ranges:
        if start <= soft_pity_count <= end:
            return pool_config.base_six_probability + boost
    
    # 不在任何特殊区间内，返回基础概率
    return pool_config.base_six_probability


def get_character_by_probability(pool_config: CharacterPoolConfig, current_probability: float = None) -> Tuple[str, int]:
    """根据概率获取一个角色
    
    参数:
        pool_config: 角色池配置
        current_probability: 当前六星概率，如果为None则使用基础概率
    
    返回:
        (角色名称, 稀有度) - 角色名称为""表示未抽中六星，稀有度为4/5/6
    """
    if current_probability is None:
        current_probability = pool_config.base_six_probability
    rand_value = random.random()
    
    # 检查是否抽中六星
    if rand_value <= current_probability:
        return get_six_star_character_by_probability(pool_config), 6
    
    # 未抽中六星，判断是4星还是5星
    # 剩余概率 = 1 - 六星概率
    remaining_prob = 1.0 - current_probability
    # 在剩余概率中，4星和5星的占比
    four_star_in_remaining = pool_config.four_star_probability / (
        pool_config.four_star_probability + pool_config.five_star_probability
    )
    
    # 在非六星中随机判断
    rand_value_2 = random.random()
    if rand_value_2 <= four_star_in_remaining:
        return "", 4  # 4星角色
    else:
        return "", 5  # 5星角色


def perform_single_character_pull(pool_config: CharacterPoolConfig, runtime_info: CharacterRuntimeInfo, 
                                   obtained_six_stars: List[str]):
    """执行单次角色池抽卡
    
    参数:
        pool_config: 角色池配置
        runtime_info: 角色池运行时信息
        obtained_six_stars: 用于记录获得的六星角色列表
    
    返回:
    """
    runtime_info.soft_pity_accumulate += 1
    runtime_info.total_pulls += 1
    runtime_info.got_five_or_six_star_character_in_next_pulls -= 1
    
    # 检查循环保底，这个是赠送，还要继续抽
    if runtime_info.total_pulls >= pool_config.loop_pity and runtime_info.total_pulls % pool_config.loop_pity == 0:
        # 直接获得一个当期UP六星
        obtained_six_stars.append("限定")
        # 这里直接给信物，应该不给武器配额
        # runtime_info.weapon_quota += pool_config.weapon_quota_per_rarity[6]
        runtime_info.soft_pity_accumulate = 0
    
    # 检查大保底
    if not runtime_info.limited_obtained and runtime_info.total_pulls == pool_config.hard_pity:
        # 获得一个当期UP六星
        obtained_six_stars.append("限定")
        runtime_info.weapon_quota += pool_config.weapon_quota_per_rarity[6]
        runtime_info.limited_obtained = True
        runtime_info.soft_pity_accumulate = 0  # 出金后重置小保底
        runtime_info.got_five_or_six_star_character_in_next_pulls = 10  # 重置N次必得
    
    # 检查小保底
    elif runtime_info.soft_pity_accumulate == pool_config.soft_pity:
        # 抽一个六星
        six_star = get_six_star_character_by_probability(pool_config)
        obtained_six_stars.append(six_star)
        runtime_info.weapon_quota += pool_config.weapon_quota_per_rarity[6]
        if six_star == "限定":
            runtime_info.limited_obtained = True
        runtime_info.soft_pity_accumulate = 0  # 出金后重置小保底
        runtime_info.got_five_or_six_star_character_in_next_pulls = 10  # 重置N次必得
    else:
        # 正常抽卡，使用区间概率提升机制
        current_probability = get_current_six_star_character_probability(pool_config, runtime_info.soft_pity_accumulate)
        character, rarity = get_character_by_probability(pool_config, current_probability)
        # 已经10发未出5星或6星，强制出一个5星
        if runtime_info.got_five_or_six_star_character_in_next_pulls <= 0 and rarity < 5:
            character = ""
            rarity = 5
        runtime_info.weapon_quota += pool_config.weapon_quota_per_rarity[rarity]
        if rarity >= 5:
            # 抽到5星或6星，重置N次必得
            runtime_info.got_five_or_six_star_character_in_next_pulls = 10
        if character == "限定":
            runtime_info.limited_obtained = True
        if character != "":
            obtained_six_stars.append(character)
            runtime_info.soft_pity_accumulate = 0  # 出金后重置小保底


def perform_ten_character_pulls(pool_config: CharacterPoolConfig, runtime_info: CharacterRuntimeInfo) -> List[str]:
    """执行一次角色池十连抽
    
    参数:
        pool_config: 角色池配置
        runtime_info: 角色池运行时信息
    
    返回:
    """
    obtained_six_stars = []
    
    # 有紧急招募且未使用，则优先使用，不需要更新小保底累计
    use_urgent_pulls = runtime_info.ten_pull_count_urgent != 0
    
    for i in range(10):
        # 非紧急招募十连，检查大保底和循环保底
        if not use_urgent_pulls:
            perform_single_character_pull(pool_config, runtime_info, obtained_six_stars)
        else:
            # 紧急招募使用基础概率（不累计大小保底和五星保底）
            current_probability = pool_config.base_six_probability
            character, rarity = get_character_by_probability(pool_config, current_probability)
            
            runtime_info.weapon_quota += pool_config.weapon_quota_per_rarity[rarity]
            if character != "":
                obtained_six_stars.append(character)
    
    if use_urgent_pulls:
        runtime_info.ten_pull_count_urgent -= 1
    elif runtime_info.ten_pull_count > 0:
        runtime_info.ten_pull_count -= 1
    
    return obtained_six_stars


def update_character_goals_achieved(goals_achieved_dict: Dict[str, int], obtained_six_stars: List[str]):
    """更新角色池已达成目标
    
    参数:
        goals_achieved_dict: 已达成目标字典
        obtained_six_stars: 获得的六星角色列表
    """
    for star in obtained_six_stars:
        goals_achieved_dict[star] = goals_achieved_dict.get(star, 0) + 1

"""
武器池抽卡工具模块 - 包含武器池抽卡相关的核心逻辑函数
"""
import random
from typing import List, Dict
from config import WeaponPoolConfig, PlayerInfo, WeaponRuntimeInfo, CharacterPoolConfig, CharacterRuntimeInfo
from character_gacha_utils import (perform_ten_character_pulls, update_character_goals_achieved, 
                                   character_goals_achieved, perform_single_character_pull)


def weapon_goals_achieved(goals_achieved_dict: Dict[str, int], goals: Dict[str, int]) -> bool:
    """检查武器池是否达成目标
    
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


def get_six_star_weapon_by_probability(pool_config: WeaponPoolConfig) -> str:
    """根据概率获取一个六星武器
    
    参数:
        pool_config: 武器池配置
    
    返回:
        六星武器名称
    """
    rand_value = random.random()
    cumulative_probability = 0.0
    for weapon, probability in pool_config.six_star_weapon_pool.items():
        cumulative_probability += probability
        if rand_value <= cumulative_probability:
            return weapon
    return list(pool_config.six_star_weapon_pool.keys())[-1]


def get_weapon_by_probability(pool_config: WeaponPoolConfig) -> tuple:
    """根据概率获取一个武器
    
    参数:
        pool_config: 武器池配置
    
    返回:
        (武器名称, 稀有度) - 武器名称为""表示未抽中六星，稀有度为5/6
    """
    rand_value = random.random()
    
    # 检查是否抽中六星武器
    if rand_value <= pool_config.base_six_probability:
        return get_six_star_weapon_by_probability(pool_config), 6
    else:
        return "", 5  # 5星武器,不具体细分了，不是六星就当5星


def perform_ten_weapon_pulls(pool_config: WeaponPoolConfig, runtime_info: WeaponRuntimeInfo) -> List[str]:
    """执行一次武器池十连抽
    
    参数:
        pool_config: 武器池配置
        runtime_info: 武器池运行时信息
    
    返回:
        obtained_six_stars: 本次十连获得的六星武器列表
    """
    obtained_six_stars = []
    
    # 检查是否有足够的武器配额
    if runtime_info.weapon_quota < pool_config.weapon_quota_cost_per_ten_pull:
        return []  # 配额不足，无法抽取
    
    # 扣除武器配额
    runtime_info.weapon_quota -= pool_config.weapon_quota_cost_per_ten_pull
    runtime_info.total_pulls += 1  # 记录十连次数
    
    # 检查特殊奖励（基于总抽数）
    if runtime_info.total_pulls == 10:
        # 第10次十连：额外获得补充武库箱
        runtime_info.supply_boxes += 1
    elif runtime_info.total_pulls == 18:
        # 第18次十连：额外送当期UP武器
        obtained_six_stars.append("限定武器")
        runtime_info.limited_obtained = True
    elif runtime_info.total_pulls > 18:
        # 第18次之后，每8次在补充武库箱和限定武器之间交替
        cycles_after_18 = runtime_info.total_pulls - 18
        if cycles_after_18 % 8 == 0:
            # 判断是奇数个8次循环还是偶数个
            cycle_number = cycles_after_18 // 8
            if cycle_number % 2 == 1:
                # 奇数次：补充武库箱（第26次）
                runtime_info.supply_boxes += 1
            else:
                # 偶数次：限定武器（第34次）
                obtained_six_stars.append("限定武器")
                runtime_info.limited_obtained = True
    
    # 正常概率抽取
    for i in range(10):
        weapon, rarity = get_weapon_by_probability(pool_config)
        if rarity == 6:
            obtained_six_stars.append(weapon)
            runtime_info.six_star_obtained = True
            if weapon == "限定武器":
                runtime_info.limited_obtained = True
    
    # 检查保底（基于总抽数和周期内是否已出）
    # 限定保底优先级高于六星保底
    if runtime_info.total_pulls == 8 and not runtime_info.limited_obtained:
        # 8次十连内未出限定，触发限定保底
        obtained_six_stars.append("限定武器")
        runtime_info.limited_obtained = True
        runtime_info.six_star_obtained = True
    elif runtime_info.total_pulls == 4 and not runtime_info.six_star_obtained:
        # 4次十连内未出六星，触发六星保底
        weapon = get_six_star_weapon_by_probability(pool_config)
        obtained_six_stars.append(weapon)
        runtime_info.six_star_obtained = True
        if weapon == "限定武器":
            runtime_info.limited_obtained = True
    
    return obtained_six_stars


def update_weapon_goals_achieved(goals_achieved_dict: Dict[str, int], obtained_six_stars: List[str]):
    """更新武器池已达成目标
    
    参数:
        goals_achieved_dict: 已达成目标字典
        obtained_six_stars: 获得的六星武器列表
    """
    for weapon in obtained_six_stars:
        goals_achieved_dict[weapon] = goals_achieved_dict.get(weapon, 0) + 1


def pull_character_for_weapon_quota(
    character_pool_config: CharacterPoolConfig,
    character_runtime_info: CharacterRuntimeInfo,
    weapon_runtime_info: WeaponRuntimeInfo,
    character_goals_achieved_dict: Dict[str, int]
) -> int:
    """通过抽取角色池来获得武器配额
    
    参数:
        character_pool_config: 角色池配置
        character_runtime_info: 角色池运行时信息
        weapon_runtime_info: 武器池运行时信息
        character_goals_achieved_dict: 角色池已达成目标字典
    
    返回:
        本次单抽使用的抽数（1）
    """
    # 将已经消耗的剩余武器配额转移到角色池运行时信息
    character_runtime_info.weapon_quota = weapon_runtime_info.weapon_quota
    # 执行角色池单抽
    obtained_six_stars = []
    perform_single_character_pull(character_pool_config, character_runtime_info, obtained_six_stars)
    
    # 更新角色池目标
    update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
    
    # 将角色池获得的武器配额转移到武器池
    weapon_runtime_info.weapon_quota = character_runtime_info.weapon_quota
    
    # 返回使用的抽数
    return 1

def combined_character_weapon_simulation(
    character_pool_config: CharacterPoolConfig,
    weapon_pool_config: WeaponPoolConfig,
    player_info: PlayerInfo
) -> Dict:
    """执行角色池+武器池的综合模拟
    
    策略：
    1. 先抽角色池直到满足角色池目标和约束
    2. 然后抽武器池，如果武器配额不足且启用了策略，则抽角色池获取配额
    3. 持续循环直到武器池目标和约束满足
    4. 如果在任何阶段达到上限，返回失败
    
    参数:
        character_pool_config: 角色池配置
        weapon_pool_config: 武器池配置
        player_info: 玩家信息
    
    返回:
        包含角色池和武器池的抽数及是否成功的字典
    """
    # 初始化运行时信息
    character_runtime_info = CharacterRuntimeInfo.from_player_info(player_info, character_pool_config)
    weapon_runtime_info = WeaponRuntimeInfo.from_player_info(player_info)
    
    # 初始化目标追踪
    character_goals_achieved_dict = {}
    weapon_goals_achieved_dict = {}
    
    # 记录抽数
    character_paid_pulls = 0  # 角色池兑换抽数
    character_free_pulls = 0  # 角色池免费十连抽数
    character_urgent_pulls = 0  # 角色池紧急招募抽数
    weapon_ten_pulls = 0  # 武器池十连次数
    extra_quota_purchased = 0  # 额外购买的武器配额数量
    
    # 确定抽数上限
    has_character_pull_limit = player_info.character_pull_limit > 0
    has_weapon_pull_limit = player_info.weapon_pull_limit > 0
    
    # ========== 阶段1: 抽角色池直到满足目标和约束 ==========
    while True:
        # 检查是否达成角色池目标
        if character_goals_achieved(character_goals_achieved_dict, player_info.character_goals):
            # 目标达成，检查是否满足最小抽数要求
            character_total_pulls = character_paid_pulls + character_free_pulls
            if character_total_pulls >= player_info.character_pull_minimum:
                break  # 满足最小抽数且达成目标，进入武器池阶段
            # 否则继续抽到满足最小抽数
        
        # 检查是否达到角色池抽数上限
        if has_character_pull_limit:
            character_total_pulls = character_paid_pulls + character_free_pulls
            if character_total_pulls >= player_info.character_pull_limit:
                # 达到上限但未达成目标，失败
                return {
                    '角色总抽数（不含紧急）': character_paid_pulls + character_free_pulls,
                    '角色紧急招募': character_urgent_pulls,
                    '角色总抽数': character_paid_pulls + character_free_pulls + character_urgent_pulls,
                    '武器十连次数': weapon_ten_pulls,
                    '武器总抽数': weapon_ten_pulls * 10,
                    '武器配额消耗': 0,
                    '剩余配额': character_runtime_info.weapon_quota,
                    '补充武库箱': 0,
                    '额外购买配额': extra_quota_purchased,
                    '成功': False,
                    '失败原因': '角色池达到上限但未满足目标'
                }
        
        # 紧急招募更新（仅当启用时）
        if (True and not character_runtime_info.urgent_recruitment_got 
            and character_runtime_info.total_pulls >= character_pool_config.urgent_recruitment_pity):
            character_runtime_info.ten_pull_count_urgent += 1
            character_runtime_info.urgent_recruitment_got = True
        
        # 是否有十连寻访凭证
        has_ten_pull = character_runtime_info.ten_pull_count > 0 or character_runtime_info.ten_pull_count_urgent > 0
        
        if has_ten_pull:
            # 记录使用哪种十连
            using_urgent = character_runtime_info.ten_pull_count_urgent > 0
            
            obtained_six_stars = perform_ten_character_pulls(character_pool_config, character_runtime_info)
            update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
            
            # 统计使用的十连类型
            if using_urgent:
                character_urgent_pulls += 10
            else:
                character_free_pulls += 10
        else:
            # 总是十连抽
            if player_info.character_always_pull_ten:
                obtained_six_stars = perform_ten_character_pulls(character_pool_config, character_runtime_info)
                update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
                character_paid_pulls += 10
            else:
                # 单抽
                obtained_six_stars = []
                perform_single_character_pull(character_pool_config, character_runtime_info, obtained_six_stars)
                update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
                character_paid_pulls += 1
    
    # 角色池阶段完成，将武器配额同步到武器池运行时信息
    weapon_runtime_info.weapon_quota = character_runtime_info.weapon_quota
    
    # ========== 阶段2: 抽武器池直到满足目标和约束 ==========
    while True:
        # 检查是否达成武器池目标
        if weapon_goals_achieved(weapon_goals_achieved_dict, player_info.weapon_goals):
            # 目标达成，检查是否满足最小抽数要求
            if weapon_ten_pulls >= player_info.weapon_pull_minimum:
                break  # 满足最小抽数且达成目标，成功
            # 否则继续抽到满足最小抽数
        
        # 检查武器池是否达到抽数上限
        if has_weapon_pull_limit and weapon_ten_pulls >= player_info.weapon_pull_limit:
            # 达到上限但未达成目标，失败
            return {
                '角色总抽数（不含紧急）': character_paid_pulls + character_free_pulls,
                '角色紧急招募': character_urgent_pulls,
                '角色总抽数': character_paid_pulls + character_free_pulls + character_urgent_pulls,
                '武器十连次数': weapon_ten_pulls,
                '武器总抽数': weapon_ten_pulls * 10,
                '武器配额消耗': weapon_ten_pulls * weapon_pool_config.weapon_quota_cost_per_ten_pull,
                '剩余配额': weapon_runtime_info.weapon_quota,
                '补充武库箱': weapon_runtime_info.supply_boxes,
                '额外购买配额': extra_quota_purchased,
                '成功': False,
                '失败原因': '武器池达到上限但未满足目标'
            }
        
        # 检查武器配额是否足够一次十连
        while weapon_runtime_info.weapon_quota < weapon_pool_config.weapon_quota_cost_per_ten_pull:
            # 检查是否启用了从角色池获取配额的策略
            if not weapon_runtime_info.is_character_pull_enabled_on_low_quota:
                # 未启用策略，直接购买武器配额
                quota_needed = weapon_pool_config.weapon_quota_cost_per_ten_pull - weapon_runtime_info.weapon_quota
                weapon_runtime_info.weapon_quota += quota_needed
                extra_quota_purchased += quota_needed
                break
            # 检查角色池是否达到抽数上限
            character_total_pulls = character_paid_pulls + character_free_pulls
            if has_character_pull_limit and character_total_pulls >= player_info.character_pull_limit:
                # 角色池达到上限，无法继续获取配额，失败
                return {
                    '角色总抽数（不含紧急）': character_paid_pulls + character_free_pulls,
                    '角色紧急招募': character_urgent_pulls,
                    '角色总抽数': character_total_pulls,
                    '武器十连次数': weapon_ten_pulls,
                    '武器总抽数': weapon_ten_pulls * 10,
                    '武器配额消耗': weapon_ten_pulls * weapon_pool_config.weapon_quota_cost_per_ten_pull,
                    '剩余配额': weapon_runtime_info.weapon_quota,
                    '补充武库箱': weapon_runtime_info.supply_boxes,
                    '额外购买配额': extra_quota_purchased,
                    '成功': False,
                    '失败原因': '角色池达到上限无法继续获取武器配额'
                }
            
            # 通过角色池获取武器配额（单抽）
            # 更新武器配额
            character_runtime_info.weapon_quota = weapon_runtime_info.weapon_quota
            # 紧急招募更新
            if (True and not character_runtime_info.urgent_recruitment_got 
                and character_runtime_info.total_pulls >= character_pool_config.urgent_recruitment_pity):
                character_runtime_info.ten_pull_count_urgent += 1
                character_runtime_info.urgent_recruitment_got = True
            
            # 是否有十连寻访凭证
            has_ten_pull = character_runtime_info.ten_pull_count > 0 or character_runtime_info.ten_pull_count_urgent > 0
            
            if has_ten_pull:
                # 记录使用哪种十连
                using_urgent = character_runtime_info.ten_pull_count_urgent > 0
                
                obtained_six_stars = perform_ten_character_pulls(character_pool_config, character_runtime_info)
                update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
                
                # 统计使用的十连类型
                if using_urgent:
                    character_urgent_pulls += 10
                else:
                    character_free_pulls += 10
            else:
                # 单抽获取武器配额
                obtained_six_stars = []
                perform_single_character_pull(character_pool_config, character_runtime_info, obtained_six_stars)
                update_character_goals_achieved(character_goals_achieved_dict, obtained_six_stars)
                character_paid_pulls += 1
            
            # 同步武器配额
            weapon_runtime_info.weapon_quota = character_runtime_info.weapon_quota
            
            # 检查是否攒够了一次武器十连的配额
            if weapon_runtime_info.weapon_quota >= weapon_pool_config.weapon_quota_cost_per_ten_pull:
                break
        
        # 再次检查配额是否足够（可能在上面的循环中失败了）
        if weapon_runtime_info.weapon_quota < weapon_pool_config.weapon_quota_cost_per_ten_pull:
            # 配额不足且无法通过角色池补充，失败
            return {
                '角色总抽数（不含紧急）': character_paid_pulls + character_free_pulls,
                '角色紧急招募': character_urgent_pulls,
                '角色总抽数': character_paid_pulls + character_free_pulls + character_urgent_pulls,
                '武器十连次数': weapon_ten_pulls,
                '武器总抽数': weapon_ten_pulls * 10,
                '武器配额消耗': weapon_ten_pulls * weapon_pool_config.weapon_quota_cost_per_ten_pull,
                '剩余配额': weapon_runtime_info.weapon_quota,
                '补充武库箱': weapon_runtime_info.supply_boxes,
                '额外购买配额': extra_quota_purchased,
                '成功': False,
                '失败原因': '武器配额不足无法继续'
            }
        
        # 执行武器池十连抽
        obtained_six_stars = perform_ten_weapon_pulls(weapon_pool_config, weapon_runtime_info)
        update_weapon_goals_achieved(weapon_goals_achieved_dict, obtained_six_stars)
        weapon_ten_pulls += 1
    
    # 判断是否成功达成目标
    success = weapon_goals_achieved(weapon_goals_achieved_dict, player_info.weapon_goals)
    
    # 计算消耗的武器配额
    weapon_quota_used = weapon_ten_pulls * weapon_pool_config.weapon_quota_cost_per_ten_pull
    
    return {
        '角色总抽数（不含紧急）': character_paid_pulls + character_free_pulls,
        '角色紧急招募': character_urgent_pulls,
        '角色总抽数': character_paid_pulls + character_free_pulls + character_urgent_pulls,
        '武器十连次数': weapon_ten_pulls,
        '武器总抽数': weapon_ten_pulls * 10,
        '武器配额消耗': weapon_quota_used,
        '剩余配额': weapon_runtime_info.weapon_quota,
        '补充武库箱': weapon_runtime_info.supply_boxes,
        '额外购买配额': extra_quota_purchased,
        '成功': success
    }

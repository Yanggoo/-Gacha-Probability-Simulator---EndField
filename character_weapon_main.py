"""
明日方舟·终末地 角色池+武器池综合抽卡概率模拟器
"""
import numpy as np
from collections import Counter
from config import CharacterPoolConfig, WeaponPoolConfig, PlayerInfo, SimulationConfig
from weapon_gacha_utils import combined_character_weapon_simulation
from analysis_utils import plot_success_failure_pie, plot_combined_distributions


def print_combined_statistics(results: list, simulation_runs: int):
    """打印综合统计信息（已禁用）
    
    参数:
        results: 模拟结果列表
        simulation_runs: 模拟次数
    """
    pass


def main():
    """主函数"""
    # 创建角色池配置
    character_pool_config = CharacterPoolConfig()
    
    # 创建武器池配置
    weapon_pool_config = WeaponPoolConfig()
    
    # 创建玩家信息
    player_info = PlayerInfo(
        # 角色池初始状态
        character_soft_pity_accumulate=0,
        character_total_pulls_used=0,
        character_limited_obtained=False,
        
        # 暴露给玩家的接口，玩家填这些信息
        got_six_star_character_in_next_pulls=10, # N次内寻访必得6星干员
        got_five_or_six_star_character_in_next_pulls=10, # N次内寻访必得5星或以上干员
        got_up_character_once_in_next_pulls=10, # 仅限一次，N次内寻访必得UP角色
        got_gifty_in_next_pulls=10, # 信物赠礼 N次寻访后可获得
        character_ten_pulls_available=0, # N张十连寻访凭证
        character_urgent_ten_pulls_available=0, # N张紧急招募十连
        initial_weapon_quota=0,  # 初始武器配额
        
        # 角色池目标和策略
        character_goals={"限定": 5},  # 目标：1个限定角色
        character_pull_limit=0,  # 抽数上限（0表示无上限）
        character_pull_minimum=0,  # 抽数下限
        character_always_pull_ten=False,  # 是否总是十连
        
        # 武器池初始状态
        weapon_total_pulls_used=0,
        weapon_limited_obtained=False,
        weapon_six_star_obtained=False,
        
        # 武器池目标和策略
        weapon_goals={"限定武器": 5},  # 目标：1个限定武器
        weapon_pull_limit=0,  # 武器池抽数上限（十连次数，0表示无上限）
        weapon_pull_minimum=0,  # 武器池抽数下限（十连次数）
        is_character_pull_enabled_on_low_quota=True  # 配额不足时抽角色池
    )
    
    # 创建模拟配置
    sim_config = SimulationConfig(simulation_runs=10000)
    
    # 运行模拟
    results = []
    success_count = 0
    failure_reasons = Counter()
    
    for i in range(sim_config.simulation_runs):
        result = combined_character_weapon_simulation(
            character_pool_config,
            weapon_pool_config,
            player_info
        )
        results.append(result)
        
        if result['成功']:
            success_count += 1
        else:
            # 统计失败原因
            failure_reason = result.get('失败原因', '未知原因')
            failure_reasons[failure_reason] += 1
    
    # 计算成功率
    failure_count = sim_config.simulation_runs - success_count
    success_rate = success_count / sim_config.simulation_runs * 100
    
    # 绘制成功率饼图
    plot_success_failure_pie(success_count, failure_count, 
                            save_path='combined_success_failure_pie.png')
    
    # 打印所有结果的统计信息
    print_combined_statistics(results, sim_config.simulation_runs)
    
    # 绘制所有结果的分布图
    plot_combined_distributions(results, success_rate, save_prefix='combined_all')


if __name__ == "__main__":
    main()

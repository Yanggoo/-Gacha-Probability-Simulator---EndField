"""
配置模块 - 定义卡池规则、玩家信息和运行时信息的数据结构
"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class CharacterPoolConfig:
    """角色池规则配置"""
    
    # 角色稀有度概率配置
    four_star_probability: float = 912.0 / 1000.0  # 4星概率 91.2%
    five_star_probability: float = 80.0 / 1000.0  # 5星概率 8%
    base_six_probability: float = 8.0 / 1000.0  # 基础六星概率 0.8%
    
    # 保底配置
    soft_pity: int = 80  # 小保底触发点：抽一个六星
    hard_pity: int = 120  # 大保底触发点：抽当期UP六星
    loop_pity: int = 240  # 循环保底触发点：直接给一个当期UP六星
    urgent_recruitment_pity: int = 30  # 加急招募赠送触发点
    
    # 六星干员池
    six_star_pool: Dict[str, float] = field(default_factory=lambda: {
        "限定": 1.0 / 2.0,  # 50%概率
        "伊冯": 1.0 / 14.0,  # 7.14%概率
        "洁哥": 1.0 / 14.0,
        "别礼": 1.0 / 14.0,
        "骏卫": 1.0 / 14.0,
        "黎风": 1.0 / 14.0,
        "小羊": 1.0 / 14.0,
        "余烬": 1.0 / 14.0
    })
    
    # 概率提升机制配置 (小保底累计抽数区间及对应的概率增加值)
    # 格式: (起始抽数, 结束抽数, 概率增加值)
    # 从66抽开始，每抽增加5%
    probability_boost_ranges: list = field(default_factory=lambda: [
        (66, 66, 0.05),   # 66抽: 提升5%
        (67, 67, 0.10),   # 67抽: 提升10%
        (68, 68, 0.15),   # 68抽: 提升15%
        (69, 69, 0.20),   # 69抽: 提升20%
        (70, 70, 0.25),   # 70抽: 提升25%
        (71, 71, 0.30),   # 71抽: 提升30%
        (72, 72, 0.35),   # 72抽: 提升35%
        (73, 73, 0.40),   # 73抽: 提升40%
        (74, 74, 0.45),   # 74抽: 提升45%
        (75, 75, 0.50),   # 75抽: 提升50%
        (76, 76, 0.55),   # 76抽: 提升55%
        (77, 77, 0.60),   # 77抽: 提升60%
        (78, 78, 0.65),   # 78抽: 提升65%
        (79, 79, 0.70),   # 79抽: 提升70%
    ])
    
    # 武器配额配置 - 根据稀有度获得的武器配额数量
    weapon_quota_per_rarity: Dict[int, int] = field(default_factory=lambda: {
        4: 20,   # 4星角色给20个武器配额
        5: 200,   # 5星角色给200个武器配额
        6: 2000   # 6星角色给2000个武器配额
    })


@dataclass
class WeaponPoolConfig:
    """武器池规则配置"""
    
    # 武器稀有度概率配置
    five_star_probability: float = 0.96  # 5星概率 96%
    base_six_probability: float = 0.04  # 基础六星武器概率 4%
    
    # 六星武器池（限定武器UP率25%，其余武器均分75%）
    six_star_weapon_pool: Dict[str, float] = field(default_factory=lambda: {
        "限定武器": 0.25,  # 25%概率
        "常驻武器1": 0.75 / 6,  # 约12.5%概率
        "常驻武器2": 0.75 / 6,
        "常驻武器3": 0.75 / 6,
        "常驻武器4": 0.75 / 6,
        "常驻武器5": 0.75 / 6,
        "常驻武器6": 0.75 / 6,
    })
    
    # 武器池特殊规则
    weapon_quota_cost_per_ten_pull: int = 1980  # 每次十连消耗1980武器配额
    only_ten_pull: bool = True  # 只能十连抽
    
    # 武器池没有小保底/大保底机制，纯概率


@dataclass
class PlayerInfo:
    """玩家信息"""
    # 内部状态字段，不暴露给UI，由compute_internal_state()自动计算
    character_soft_pity_accumulate: int = 0  # 角色池小保底当前累计抽数
    
    # 暴露给玩家的接口，玩家填以下这些信息
    got_six_star_character_in_next_pulls: int = 80  # N次内寻访必得6星干员
    got_five_or_six_star_character_in_next_pulls: int = 10  # N次内寻访必得5星或以上干员
    character_total_pulls_used: int = 0  # 角色池当前已经使用的抽数
    character_limited_obtained: bool = False  # 是否已经获得限定角色
    character_ten_pulls_available: int = 0  # N张十连寻访凭证
    character_urgent_ten_pulls_available: int = 0  # N张紧急招募十连
    initial_weapon_quota: int = 0  # 初始武器配额
    
    # 角色池目标和策略
    character_goals: Dict[str, int] = field(default_factory=lambda: {"限定": 1})
    character_always_pull_ten: bool = False  # 角色池是否总是进行十连抽
    character_pull_limit: int = 0  # 抽数上限，0表示无上限，必能抽到
    character_pull_minimum: int = 0  # 抽数下限，用于获取奖励（如30抽的紧急招募，60抽的下期十连）
    
    # 武器池信息
    weapon_total_pulls_used: int = 0  # 武器池当前已经使用的抽数（十连数）
    weapon_limited_obtained: bool = False  # 是否已经获得限定武器
    weapon_six_star_obtained: bool = False  # 是否已经获得六星武器
    
    # 武器池目标和策略
    weapon_goals: Dict[str, int] = field(default_factory=lambda: {"限定武器": 1})
    weapon_pull_limit: int = 0  # 抽数上限（十连次数），0表示无上限，必能抽到
    weapon_pull_minimum: int = 0  # 抽数下限（十连次数）
    is_character_pull_enabled_on_low_quota: bool = True  # 是否在武器配额不足时抽取角色以获取配额
    
    def compute_internal_state(self, pool_config: CharacterPoolConfig):
        """根据已填信息计算内部状态字段
        
        该方法根据玩家填写的保底信息推算当前的内部状态：
        - character_soft_pity_accumulate: 小保底累计抽数
        
        参数:
            pool_config: 角色池配置
        """
        # 根据"N次内必得6星"推算小保底累计
        self.character_soft_pity_accumulate = pool_config.soft_pity - self.got_six_star_character_in_next_pulls
        # 如果不是正数，程序要报错，通知玩家填错了
        if self.character_soft_pity_accumulate < 0:
            raise ValueError(self.got_six_star_character_in_next_pulls, "小保底累计抽数计算错误，请检查“N次内必得6星”填写是否正确")
        


@dataclass
class WeaponRuntimeInfo:
    """武器池运行时信息 - 单次模拟运行期间的状态"""
    
    total_pulls: int = 0  # 当前总抽数（十连次数）
    limited_obtained: bool = False  # 是否已获得限定武器
    six_star_obtained: bool = False  # 是否已出六星
    weapon_quota: int = 0  # 当前剩余武器配额
    supply_boxes: int = 0  # 获得的补充武库箱数量
    is_character_pull_enabled_on_low_quota: bool = True  # 是否在武器配额不足时抽取角色以获取配额

    
    @classmethod
    def from_player_info(cls, player_info: PlayerInfo):
        """从玩家信息创建武器池运行时信息"""
        return cls(
            total_pulls=player_info.weapon_total_pulls_used,
            limited_obtained=player_info.weapon_limited_obtained,
            six_star_obtained=player_info.weapon_six_star_obtained,
            weapon_quota=player_info.initial_weapon_quota,
            supply_boxes=0,
            is_character_pull_enabled_on_low_quota=player_info.is_character_pull_enabled_on_low_quota,
        )


@dataclass
class CharacterRuntimeInfo:
    """角色池运行时信息 - 单次模拟运行期间的状态"""
    
    soft_pity_accumulate: int = 0  # 当前小保底累计
    total_pulls: int = 0  # 当前总抽数
    limited_obtained: bool = False  # 是否已获得限定
    weapon_quota: int = 0  # 当前武器配额
    ten_pull_count: int = 0  # 免费十连数量
    ten_pull_count_urgent: int = 0  # 紧急招募十连数量
    urgent_recruitment_got: bool = False  # 是否已获得紧急招募
    got_five_or_six_star_character_in_next_pulls: int = 0  # N次寻访内必得5星或6星角色
    
    @classmethod
    def from_player_info(cls, player_info: PlayerInfo, pool_config: CharacterPoolConfig):
        """从玩家信息创建角色池运行时信息"""
        # 判断是否有紧急招募（根据已使用抽数或已有紧急十连）
        has_urgent = (True and player_info.character_total_pulls_used >= pool_config.urgent_recruitment_pity 
            or player_info.character_urgent_ten_pulls_available > 0
        )
        
        return cls(
            soft_pity_accumulate=player_info.character_soft_pity_accumulate,
            total_pulls=player_info.character_total_pulls_used,
            limited_obtained=player_info.character_limited_obtained,
            weapon_quota=player_info.initial_weapon_quota,
            ten_pull_count=player_info.character_ten_pulls_available,
            ten_pull_count_urgent=player_info.character_urgent_ten_pulls_available,
            urgent_recruitment_got=has_urgent,
            got_five_or_six_star_character_in_next_pulls=player_info.got_five_or_six_star_character_in_next_pulls
        )


@dataclass
class SimulationConfig:
    """模拟配置"""
    
    simulation_runs: int = 10000  # 模拟次数

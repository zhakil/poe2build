#!/usr/bin/env python3
"""
PoE2 AI协调器主程序 - Path of Exile 2 Build Generator

这是PoE2构筑生成器的主要入口点，集成了：
- RAG增强的AI构筑推荐
- PoB2本地/Web集成
- 实时市场数据
- 智能推荐引擎

使用示例:
    python poe2_ai_orchestrator.py --help
    python poe2_ai_orchestrator.py --interactive
    python poe2_ai_orchestrator.py --class ranger --goal boss_killing --budget 15
    python poe2_ai_orchestrator.py --demo
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from poe2build.core.ai_orchestrator import (
    PoE2AIOrchestrator, UserRequest, RecommendationResult,
    SystemComponent, ComponentStatus
)
from poe2build.core.build_generator import (
    PoE2BuildGenerator, GenerationConstraints, BuildComplexity
)
from poe2build.core.recommender import (
    PoE2Recommender, RecommendationRequest, ScoringWeights
)
from poe2build.models.build import PoE2BuildGoal
from poe2build.models.characters import PoE2CharacterClass, PoE2Ascendancy


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/poe2_orchestrator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class PoE2CLI:
    """PoE2构筑生成器命令行界面"""
    
    def __init__(self):
        """初始化CLI"""
        self.orchestrator = None
        self.generator = None
        self.recommender = None
        self.config = self._load_config()
        
        # 确保日志目录存在
        Path("logs").mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        config_file = Path("config/app_config.json")
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"配置文件加载失败: {e}")
        
        # 默认配置
        return {
            "max_recommendations": 10,
            "default_budget": 15.0,
            "cache_ttl": 3600,
            "pob2": {
                "enable_local": True,
                "enable_web": True
            },
            "rag": {
                "confidence_threshold": 0.7
            },
            "market": {
                "update_interval": 600
            }
        }
    
    async def initialize(self) -> bool:
        """初始化所有组件"""
        logger.info("[INIT] Initializing PoE2 Build Generator...")
        
        try:
            # 初始化AI协调器
            self.orchestrator = PoE2AIOrchestrator(self.config)
            await self.orchestrator.initialize()
            
            # 初始化构筑生成器
            self.generator = PoE2BuildGenerator(self.config.get('generator', {}))
            
            # 初始化推荐引擎
            self.recommender = PoE2Recommender(self.config.get('recommender', {}))
            
            logger.info("[INIT] All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"[ERROR] Initialization failed: {e}")
            return False
    
    async def run_health_check(self) -> bool:
        """运行系统健康检查"""
        logger.info("[HEALTH] Executing system health check...")
        
        if not self.orchestrator:
            logger.error("[ERROR] Orchestrator not initialized")
            return False
        
        health_report = await self.orchestrator.health_check()
        
        print("\n" + "="*60)
        print("System Health Check Report")
        print("="*60)
        
        # 显示总体状态
        status_emoji = {
            'healthy': '[OK]',
            'degraded': '[WARN]', 
            'unhealthy': '[ERROR]'
        }
        
        overall_status = health_report['overall_status']
        print(f"Overall Status: {status_emoji.get(overall_status, '[UNKNOWN]')} {overall_status.upper()}")
        print()
        
        # 显示组件状态
        print("Component Status:")
        for component, info in health_report['components'].items():
            status = info['status']
            emoji = '[OK]' if status == 'healthy' else ('[WARN]' if status == 'degraded' else '[ERROR]')
            
            response_time = info.get('response_time_ms')
            time_str = f" ({response_time:.1f}ms)" if response_time else ""
            
            print(f"  {emoji} {component}: {status}{time_str}")
            
            if info.get('error_message'):
                print(f"    WARNING: {info['error_message']}")
        
        # 显示性能指标
        print("\nPerformance Metrics:")
        perf = health_report['performance']
        print(f"  Total Requests: {perf['total_requests']}")
        print(f"  Error Count: {perf['error_count']}")
        print(f"  Average Response Time: {perf['average_response_time_ms']:.2f}ms")
        print(f"  Error Rate: {perf['error_rate']:.2%}")
        
        print("="*60)
        
        return overall_status in ['healthy', 'degraded']
    
    async def run_interactive_mode(self):
        """运行交互式模式"""
        print("\n[INTERACTIVE] Welcome to PoE2 Build Generator!")
        print("Type 'help' for commands, 'quit' to exit")
        
        while True:
            try:
                command = input("\npoe2> ").strip().lower()
                
                if command in ['quit', 'exit', 'q']:
                    print("Goodbye!")
                    break
                elif command == 'help':
                    self._show_interactive_help()
                elif command == 'health':
                    await self.run_health_check()
                elif command == 'demo':
                    await self.run_demo()
                elif command.startswith('generate'):
                    await self._handle_generate_command(command)
                elif command.startswith('recommend'):
                    await self._handle_recommend_command(command)
                elif command == 'stats':
                    self._show_system_stats()
                else:
                    print(f"Unknown command: {command}, type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                logger.exception("Interactive mode error")
    
    def _show_interactive_help(self):
        """显示交互式模式帮助"""
        help_text = """
🆘 可用命令:

基础命令:
  help              - 显示此帮助信息
  health            - 执行系统健康检查
  stats             - 显示系统统计信息
  demo              - 运行演示
  quit              - 退出程序

构筑生成:
  generate          - 生成构筑（会提示输入参数）
  generate ranger   - 为Ranger职业生成构筑
  
推荐系统:
  recommend         - 获取构筑推荐（会提示输入参数）

示例:
  poe2> generate ranger
  poe2> health
  poe2> demo
"""
        print(help_text)
    
    async def _handle_generate_command(self, command: str):
        """处理生成命令"""
        parts = command.split()
        
        if len(parts) == 1:
            # 交互式生成
            await self._interactive_generate()
        else:
            # 解析参数生成
            class_name = parts[1] if len(parts) > 1 else None
            await self._generate_with_class(class_name)
    
    async def _interactive_generate(self):
        """交互式构筑生成"""
        print("\n🔧 构筑生成器")
        
        try:
            # 选择职业
            print("\n可用职业:")
            for i, char_class in enumerate(PoE2CharacterClass, 1):
                print(f"  {i}. {char_class.value}")
            
            class_choice = input("选择职业 (编号或名称): ").strip()
            character_class = self._parse_character_class(class_choice)
            
            if not character_class:
                print("❌ 无效的职业选择")
                return
            
            # 选择目标
            print("\n构筑目标:")
            for i, goal in enumerate(PoE2BuildGoal, 1):
                print(f"  {i}. {goal.value}")
            
            goal_choice = input("选择目标 (编号或名称, 默认: endgame_content): ").strip()
            build_goal = self._parse_build_goal(goal_choice) or PoE2BuildGoal.ENDGAME_CONTENT
            
            # 预算
            budget_input = input("最大预算 (divine, 默认: 15): ").strip()
            max_budget = float(budget_input) if budget_input else 15.0
            
            # 数量
            count_input = input("生成数量 (默认: 3): ").strip()
            count = int(count_input) if count_input else 3
            
            # 生成构筑
            await self._generate_builds(character_class, build_goal, max_budget, count)
            
        except Exception as e:
            print(f"❌ 生成失败: {e}")
            logger.exception("交互式生成错误")
    
    async def _generate_with_class(self, class_name: Optional[str]):
        """为指定职业生成构筑"""
        if not class_name:
            await self._interactive_generate()
            return
        
        character_class = self._parse_character_class(class_name)
        if not character_class:
            print(f"❌ 无效的职业: {class_name}")
            return
        
        # 使用默认参数
        await self._generate_builds(
            character_class=character_class,
            build_goal=PoE2BuildGoal.ENDGAME_CONTENT,
            max_budget=15.0,
            count=3
        )
    
    async def _generate_builds(self, character_class: PoE2CharacterClass, 
                             build_goal: PoE2BuildGoal, 
                             max_budget: float, 
                             count: int):
        """生成构筑"""
        print(f"\n[GENERATE] Creating {character_class.value} builds...")
        print(f"Goal: {build_goal.value}, Budget: {max_budget} divine, Count: {count}")
        
        try:
            start_time = time.time()
            
            # 创建生成约束
            constraints = GenerationConstraints(
                max_budget=max_budget,
                min_dps=300000,
                min_ehp=4000,
                required_resistances={"fire": 75, "cold": 75, "lightning": 75},
                complexity_limit=BuildComplexity.INTERMEDIATE
            )
            
            # 生成构筑
            builds = await self.generator.generate_builds(
                character_class=character_class,
                build_goal=build_goal,
                constraints=constraints,
                count=count
            )
            
            generation_time = time.time() - start_time
            
            if not builds:
                print("[ERROR] Failed to generate any builds")
                return
            
            print(f"\n[SUCCESS] Generation completed! ({generation_time:.2f}s)")
            print(f"Generated {len(builds)} builds:")
            
            # 显示构筑
            for i, build in enumerate(builds, 1):
                self._display_build_summary(i, build)
            
            # 询问是否查看详情
            choice = input("\nView build details? (number, or 'skip'): ").strip()
            if choice.isdigit():
                build_index = int(choice) - 1
                if 0 <= build_index < len(builds):
                    self._display_build_details(builds[build_index])
            
        except Exception as e:
            print(f"[ERROR] Generation failed: {e}")
            logger.exception("Build generation error")
    
    async def _handle_recommend_command(self, command: str):
        """处理推荐命令"""
        print("\n[RECOMMEND] Build Recommendation System")
        
        try:
            # 简化的推荐流程
            print("Using example recommendation parameters...")
            
            # 创建用户请求
            user_request = UserRequest(
                character_class=PoE2CharacterClass.RANGER,
                build_goal=PoE2BuildGoal.CLEAR_SPEED,
                max_budget=20.0,
                min_dps=500000,
                min_ehp=5000,
                generate_pob2_code=True,
                validate_with_pob2=True
            )
            
            # 生成推荐
            print("[PROGRESS] Generating recommendations...")
            result = await self.orchestrator.generate_build_recommendations(user_request)
            
            if result.builds:
                print(f"\n[SUCCESS] Recommendation completed! Found {len(result.builds)} recommended builds:")
                print(f"RAG Confidence: {result.rag_confidence:.3f}")
                print(f"PoB2 Validated: {'[OK]' if result.pob2_validated else '[NO]'}")
                print(f"Generation Time: {result.generation_time_ms:.2f}ms")
                
                for i, build in enumerate(result.builds, 1):
                    self._display_build_summary(i, build)
            else:
                print("[ERROR] No suitable recommendations found")
                
        except Exception as e:
            print(f"[ERROR] Recommendation failed: {e}")
            logger.exception("Recommendation error")
    
    def _display_build_summary(self, index: int, build):
        """显示构筑摘要"""
        print(f"\n{index}. {build.name}")
        print(f"   Class: {build.character_class.value}")
        if build.ascendancy:
            print(f"   Ascendancy: {build.ascendancy.value}")
        print(f"   Level: {build.level}")
        if build.stats:
            print(f"   DPS: {build.stats.total_dps:,.0f}")
            print(f"   EHP: {build.stats.effective_health_pool:,.0f}")
            res_status = "[OK]" if build.stats.is_resistance_capped() else "[LOW]"
            print(f"   Resistances: {res_status}")
        if build.estimated_cost:
            print(f"   Cost: {build.estimated_cost} divine")
        if build.main_skill_gem:
            print(f"   Main Skill: {build.main_skill_gem}")
    
    def _display_build_details(self, build):
        """显示构筑详细信息"""
        print(f"\n{'='*50}")
        print(f"构筑详情: {build.name}")
        print(f"{'='*50}")
        
        print(f"职业: {build.character_class.value}")
        if build.ascendancy:
            print(f"升华: {build.ascendancy.value}")
        print(f"等级: {build.level}")
        
        if build.stats:
            print(f"\n📊 统计数据:")
            print(f"  总DPS: {build.stats.total_dps:,.0f}")
            print(f"  有效生命: {build.stats.effective_health_pool:,.0f}")
            print(f"  生命: {build.stats.life:,.0f}")
            print(f"  护盾: {build.stats.energy_shield:,.0f}")
            print(f"  火焰抗性: {build.stats.fire_resistance}%")
            print(f"  冰霜抗性: {build.stats.cold_resistance}%") 
            print(f"  闪电抗性: {build.stats.lightning_resistance}%")
            print(f"  混沌抗性: {build.stats.chaos_resistance}%")
        
        if build.estimated_cost:
            print(f"\n💰 预估成本: {build.estimated_cost} {build.currency_type}")
        
        if build.main_skill_gem:
            print(f"\n🎯 主要技能: {build.main_skill_gem}")
        
        if build.support_gems:
            print(f"⚡ 辅助宝石: {', '.join(build.support_gems)}")
        
        if build.key_items:
            print(f"🛡️  关键装备: {', '.join(build.key_items)}")
        
        if build.passive_keystones:
            print(f"🔮 关键天赋: {', '.join(build.passive_keystones)}")
        
        if build.pob2_code:
            print(f"\n📋 PoB2导入代码: {build.pob2_code}")
        
        if build.notes:
            print(f"\n📝 备注: {build.notes}")
    
    def _show_system_stats(self):
        """显示系统统计信息"""
        if not self.orchestrator:
            print("[ERROR] Orchestrator not initialized")
            return
        
        stats = self.orchestrator.get_system_stats()
        
        print(f"\n[STATS] System Statistics:")
        print(f"  Initialized: {'[OK]' if stats['initialized'] else '[NO]'}")
        print(f"  Total Requests: {stats['request_count']}")
        print(f"  Error Count: {stats['error_count']}")
        print(f"  Success Rate: {stats['success_rate']:.2%}")
        print(f"  Average Response Time: {stats['average_response_time_ms']:.2f}ms")
        print(f"  Total Components: {stats['component_count']}")
        print(f"  Healthy Components: {stats['healthy_components']}")
    
    async def run_demo(self):
        """运行演示"""
        print("\n[DEMO] PoE2 Build Generator Demonstration")
        print("="*50)
        
        demos = [
            ("System Health Check", self._demo_health_check),
            ("Ranger Bow Build Generation", self._demo_ranger_builds),
            ("Witch Caster Recommendations", self._demo_witch_recommendations),
            ("Budget-Friendly Builds", self._demo_budget_builds),
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n[DEMO] {demo_name}")
            print("-" * 30)
            try:
                await demo_func()
                print("[SUCCESS] Demo completed")
            except Exception as e:
                print(f"[ERROR] Demo failed: {e}")
            
            input("Press Enter to continue...")
    
    async def _demo_health_check(self):
        """演示健康检查"""
        await self.run_health_check()
    
    async def _demo_ranger_builds(self):
        """演示Ranger构筑生成"""
        await self._generate_builds(
            character_class=PoE2CharacterClass.RANGER,
            build_goal=PoE2BuildGoal.CLEAR_SPEED,
            max_budget=15.0,
            count=2
        )
    
    async def _demo_witch_recommendations(self):
        """演示Witch构筑推荐"""
        user_request = UserRequest(
            character_class=PoE2CharacterClass.WITCH,
            build_goal=PoE2BuildGoal.BOSS_KILLING,
            max_budget=25.0,
            min_dps=800000,
            generate_pob2_code=True
        )
        
        result = await self.orchestrator.generate_build_recommendations(user_request)
        
        if result.builds:
            print(f"Found {len(result.builds)} recommendations:")
            for i, build in enumerate(result.builds[:2], 1):
                self._display_build_summary(i, build)
    
    async def _demo_budget_builds(self):
        """演示预算构筑"""
        await self._generate_builds(
            character_class=PoE2CharacterClass.WARRIOR,
            build_goal=PoE2BuildGoal.BUDGET_FRIENDLY,
            max_budget=5.0,
            count=2
        )
    
    def _parse_character_class(self, input_str: str) -> Optional[PoE2CharacterClass]:
        """解析角色职业"""
        if not input_str:
            return None
        
        input_str = input_str.strip().lower()
        
        # 尝试按编号
        try:
            index = int(input_str) - 1
            classes = list(PoE2CharacterClass)
            if 0 <= index < len(classes):
                return classes[index]
        except ValueError:
            pass
        
        # 尝试按名称
        for char_class in PoE2CharacterClass:
            if char_class.value.lower() == input_str:
                return char_class
        
        return None
    
    def _parse_build_goal(self, input_str: str) -> Optional[PoE2BuildGoal]:
        """解析构筑目标"""
        if not input_str:
            return None
        
        input_str = input_str.strip().lower()
        
        # 尝试按编号
        try:
            index = int(input_str) - 1
            goals = list(PoE2BuildGoal)
            if 0 <= index < len(goals):
                return goals[index]
        except ValueError:
            pass
        
        # 尝试按名称
        for goal in PoE2BuildGoal:
            if goal.value.lower() == input_str:
                return goal
        
        return None


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PoE2 AI构筑生成器 - 智能构筑推荐系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s --interactive                    # 交互式模式
  %(prog)s --health                         # 系统健康检查
  %(prog)s --demo                           # 运行演示
  %(prog)s --class ranger --goal clear_speed --budget 15   # 快速生成
  %(prog)s --class witch --goal boss_killing --budget 30   # Boss击杀构筑

支持的职业: witch, ranger, warrior, monk, mercenary, sorceress
支持的目标: clear_speed, boss_killing, endgame_content, league_start, budget_friendly
        """
    )
    
    # 运行模式
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='运行交互式模式')
    parser.add_argument('--health', action='store_true',
                       help='执行系统健康检查')
    parser.add_argument('--demo', action='store_true',
                       help='运行演示')
    
    # 构筑生成参数
    parser.add_argument('--class', '-c', dest='character_class',
                       choices=['witch', 'ranger', 'warrior', 'monk', 'mercenary', 'sorceress'],
                       help='角色职业')
    parser.add_argument('--goal', '-g',
                       choices=['clear_speed', 'boss_killing', 'endgame_content', 'league_start', 'budget_friendly'],
                       help='构筑目标')
    parser.add_argument('--budget', '-b', type=float, default=15.0,
                       help='最大预算 (divine orbs, 默认: 15)')
    parser.add_argument('--count', '-n', type=int, default=3,
                       help='生成构筑数量 (默认: 3)')
    
    # 其他选项
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='详细输出')
    parser.add_argument('--config', type=Path,
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建CLI实例
    cli = PoE2CLI()
    
    # 初始化系统
    init_success = await cli.initialize()
    if not init_success:
        print("System initialization failed, exiting")
        return 1
    
    try:
        # 根据参数执行相应功能
        if args.health:
            success = await cli.run_health_check()
            return 0 if success else 1
        
        elif args.demo:
            await cli.run_demo()
            return 0
        
        elif args.interactive:
            await cli.run_interactive_mode()
            return 0
        
        elif args.character_class:
            # 命令行构筑生成
            character_class = cli._parse_character_class(args.character_class)
            build_goal = cli._parse_build_goal(args.goal) if args.goal else PoE2BuildGoal.ENDGAME_CONTENT
            
            await cli._generate_builds(
                character_class=character_class,
                build_goal=build_goal,
                max_budget=args.budget,
                count=args.count
            )
            return 0
        
        else:
            # 默认运行交互式模式
            print("No mode specified, starting interactive mode...")
            await cli.run_interactive_mode()
            return 0
    
    except KeyboardInterrupt:
        print("\nUser interrupted, exiting")
        return 0
    except Exception as e:
        logger.exception("Program execution error")
        print(f"Program error: {e}")
        return 1


if __name__ == "__main__":
    # 确保在Windows上正确处理asyncio
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
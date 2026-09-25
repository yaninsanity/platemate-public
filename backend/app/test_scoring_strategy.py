"""
🧪 评分策略重构测试脚本

测试目标：
1. 验证策略配置正确加载
2. 验证两种模式的配置差异
3. 验证后处理转换逻辑
"""

import sys
from pathlib import Path
import os

# 添加backend路径
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'app.settings')
import django
django.setup()

from cookai.backend import OpenAIBackend
from system.models import SystemConfig


def test_strategy_structure():
    """测试策略配置结构完整性"""
    print("\n🧪 测试1: 策略配置结构")
    print("-" * 50)
    
    strategy = OpenAIBackend._get_scoring_strategy()
    
    required_keys = [
        'mode',
        'tone_guide', 
        'forbidden_words',
        'score_guidelines',
        'response_tone',
        'apply_score_transformation',
        'apply_irb_compliance'
    ]
    
    for key in required_keys:
        assert key in strategy, f"❌ 缺少必需的配置: {key}"
        print(f"✅ {key}: 存在")
    
    print("\n✅ 策略配置结构完整")


def test_nice_guy_mode():
    """测试好人卡模式配置"""
    print("\n🧪 测试2: 好人卡模式配置")
    print("-" * 50)
    
    # 获取或创建配置
    config = SystemConfig.get_config()
    config.nice_guy_card_mode = True
    config.save()
    
    strategy = OpenAIBackend._get_scoring_strategy()
    
    print(f"模式: {strategy['mode']}")
    assert strategy['mode'] == 'nice_guy', "❌ 模式应该是 nice_guy"
    print("✅ 模式正确")
    
    assert strategy['apply_score_transformation'] == True, "❌ 应该启用分数转换"
    print("✅ 分数转换: 启用")
    
    assert strategy['apply_irb_compliance'] == True, "❌ 应该启用IRB合规"
    print("✅ IRB合规: 启用")
    
    assert 'NICE GUY' in strategy['tone_guide'], "❌ tone_guide应包含NICE GUY"
    print("✅ Prompt指令正确")
    
    print("\n✅ 好人卡模式配置正确")


def test_real_feedback_mode():
    """测试真实反馈模式配置"""
    print("\n🧪 测试3: 真实反馈模式配置")
    print("-" * 50)
    
    # 关闭好人卡模式
    config = SystemConfig.get_config()
    config.nice_guy_card_mode = False
    config.save()
    
    strategy = OpenAIBackend._get_scoring_strategy()
    
    print(f"模式: {strategy['mode']}")
    assert strategy['mode'] == 'real_feedback', "❌ 模式应该是 real_feedback"
    print("✅ 模式正确")
    
    assert strategy['apply_score_transformation'] == False, "❌ 不应该启用分数转换"
    print("✅ 分数转换: 禁用")
    
    assert strategy['apply_irb_compliance'] == False, "❌ 不应该启用IRB合规"
    print("✅ IRB合规: 禁用")
    
    assert 'REAL FEEDBACK' in strategy['tone_guide'], "❌ tone_guide应包含REAL FEEDBACK"
    print("✅ Prompt指令正确")
    
    print("\n✅ 真实反馈模式配置正确")


def test_transformation_logic():
    """测试后处理转换逻辑"""
    print("\n🧪 测试4: 后处理转换逻辑")
    print("-" * 50)
    
    # 测试数据
    test_result = {
        'overall_score': 60.0,
        'visual_appeal': 55.0,
        'cooking_technique': 50.0,
        'ingredient_freshness': 65.0,
        'creativity_innovation': 58.0,
        'nutrition_balance': 62.0,
        'ai_comment': 'This needs work and is unclear',
        'ai_summary': 'Needs improvement',
        'confidence': 0.7,
        'mastery_level': 'Beginner',
        'improvement_tips': []
    }
    
    # 测试好人卡模式转换
    nice_guy_strategy = {
        'mode': 'nice_guy',
        'apply_score_transformation': True,
        'apply_irb_compliance': True
    }
    
    transformed = OpenAIBackend._apply_scoring_transformations(
        test_result.copy(), 
        nice_guy_strategy
    )
    
    print(f"原始分数: {test_result['overall_score']}")
    print(f"转换后分数: {transformed['overall_score']}")
    assert transformed['overall_score'] >= 80.0, "❌ 好人卡模式应该转换到80-100"
    print("✅ 分数转换正确 (0-100 → 80-100)")
    
    # 测试真实反馈模式（不转换）
    real_strategy = {
        'mode': 'real_feedback',
        'apply_score_transformation': False,
        'apply_irb_compliance': False
    }
    
    preserved = OpenAIBackend._apply_scoring_transformations(
        test_result.copy(),
        real_strategy
    )
    
    print(f"\n原始分数: {test_result['overall_score']}")
    print(f"真实模式分数: {preserved['overall_score']}")
    assert preserved['overall_score'] == 60.0, "❌ 真实模式应该保持原分数"
    print("✅ 真实模式保持原分数")
    
    print("\n✅ 后处理转换逻辑正确")


def test_mode_consistency():
    """测试模式一致性（确保只检查一次）"""
    print("\n🧪 测试5: 模式一致性验证")
    print("-" * 50)
    
    # 开启好人卡模式
    config = SystemConfig.get_config()
    config.nice_guy_card_mode = True
    config.save()
    
    # 获取策略
    strategy = OpenAIBackend._get_scoring_strategy()
    
    # 验证Prompt策略和后处理策略一致
    print(f"Prompt模式: {strategy['mode']}")
    print(f"分数转换: {strategy['apply_score_transformation']}")
    print(f"IRB合规: {strategy['apply_irb_compliance']}")
    
    if strategy['mode'] == 'nice_guy':
        assert strategy['apply_score_transformation'] == True
        assert strategy['apply_irb_compliance'] == True
        print("✅ 好人卡模式：Prompt和后处理配置一致")
    
    # 关闭好人卡模式
    config.nice_guy_card_mode = False
    config.save()
    
    strategy = OpenAIBackend._get_scoring_strategy()
    
    print(f"\nPrompt模式: {strategy['mode']}")
    print(f"分数转换: {strategy['apply_score_transformation']}")
    print(f"IRB合规: {strategy['apply_irb_compliance']}")
    
    if strategy['mode'] == 'real_feedback':
        assert strategy['apply_score_transformation'] == False
        assert strategy['apply_irb_compliance'] == False
        print("✅ 真实反馈模式：Prompt和后处理配置一致")
    
    print("\n✅ 模式一致性验证通过")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("🚀 评分策略重构测试")
    print("=" * 60)
    
    try:
        test_strategy_structure()
        test_nice_guy_mode()
        test_real_feedback_mode()
        test_transformation_logic()
        test_mode_consistency()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试通过！")
        print("=" * 60)
        print("\n🎯 重构成功验证：")
        print("  • 策略配置结构完整")
        print("  • 两种模式配置正确")
        print("  • 后处理转换逻辑正确")
        print("  • 模式一致性保证")
        print("  • 职责分离清晰")
        print("\n")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n🚨 测试出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

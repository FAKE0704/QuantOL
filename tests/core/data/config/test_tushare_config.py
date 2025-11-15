"""
TushareConfig测试
测试tushare配置管理器的各项功能
"""

import unittest
import os
import json
import tempfile
from pathlib import Path
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from src.core.data.config.tushare_config import TushareConfig, TushareServiceError


class TestTushareConfig(unittest.TestCase):
    """TushareConfig测试类"""

    def setUp(self):
        """测试前设置"""
        self.test_token = "test_token_12345"
        self.valid_config = {
            'token': self.test_token,
            'cache_enabled': True,
            'cache_ttl': 3600,
            'cache_dir': './test_cache',
            'rate_limit': 120,
            'retry_times': 3,
            'timeout': 30,
            'min_request_interval': 0.5,
            'max_request_interval': 2.0,
            'log_level': 'INFO',
            'log_requests': False,
            'default_start_date': '20200101',
            'max_records_per_request': 5000,
            'save_to_db': True,
            'db_batch_size': 1000,
            'user_agent': 'TushareClient/1.0',
            'proxy_url': None
        }

    def test_init_valid_config(self):
        """测试有效配置的初始化"""
        config = TushareConfig(token=self.test_token)

        self.assertEqual(config.token, self.test_token)
        self.assertTrue(config.cache_enabled)
        self.assertEqual(config.cache_ttl, 3600)
        self.assertEqual(config.rate_limit, 120)

    def test_from_env_valid(self):
        """测试从环境变量加载有效配置"""
        # 设置环境变量
        env_vars = {
            'TUSHARE_TOKEN': self.test_token,
            'TUSHARE_CACHE_ENABLED': 'true',
            'TUSHARE_CACHE_TTL': '7200',
            'TUSHARE_RATE_LIMIT': '200',
            'TUSHARE_LOG_LEVEL': 'DEBUG',
            'TUSHARE_LOG_REQUESTS': '1'
        }

        with unittest.mock.patch.dict(os.environ, env_vars):
            config = TushareConfig.from_env()

            self.assertEqual(config.token, self.test_token)
            self.assertTrue(config.cache_enabled)
            self.assertEqual(config.cache_ttl, 7200)
            self.assertEqual(config.rate_limit, 200)
            self.assertEqual(config.log_level, 'DEBUG')
            self.assertTrue(config.log_requests)

    def test_from_env_missing_token(self):
        """测试环境变量缺少token的情况"""
        env_vars = {
            'TUSHARE_CACHE_ENABLED': 'true'
        }

        with unittest.mock.patch.dict(os.environ, env_vars, clear=True):
            with self.assertRaises(ValueError):
                TushareConfig.from_env()

    def test_from_file_valid(self):
        """测试从文件加载有效配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(self.valid_config, f)
            temp_file = f.name

        try:
            config = TushareConfig.from_file(temp_file)

            self.assertEqual(config.token, self.test_token)
            self.assertTrue(config.cache_enabled)
            self.assertEqual(config.cache_ttl, 3600)
        finally:
            os.unlink(temp_file)

    def test_from_file_not_exists(self):
        """测试文件不存在的情况"""
        with self.assertRaises(FileNotFoundError):
            TushareConfig.from_file('/nonexistent/file.json')

    def test_from_file_invalid_json(self):
        """测试无效JSON文件的情况"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write('invalid json content')
            temp_file = f.name

        try:
            with self.assertRaises(ValueError):
                TushareConfig.from_file(temp_file)
        finally:
            os.unlink(temp_file)

    def test_save_to_file(self):
        """测试保存配置到文件"""
        config = TushareConfig(**self.valid_config)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            result = config.save_to_file(temp_file)
            self.assertTrue(result)

            # 验证文件内容
            with open(temp_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)

            self.assertEqual(loaded_data['token'], self.test_token)
            self.assertTrue(loaded_data['cache_enabled'])
        finally:
            os.unlink(temp_file)

    def test_validate_valid_config(self):
        """测试有效配置的验证"""
        config = TushareConfig(**self.valid_config)
        self.assertTrue(config.validate())

    def test_validate_empty_token(self):
        """测试空token的验证"""
        config_data = self.valid_config.copy()
        config_data['token'] = ''

        with self.assertRaises(ValueError):
            TushareConfig(**config_data)

    def test_validate_negative_ttl(self):
        """测试负缓存时间的验证"""
        config_data = self.valid_config.copy()
        config_data['cache_ttl'] = -1

        with self.assertRaises(ValueError):
            TushareConfig(**config_data)

    def test_validate_invalid_log_level(self):
        """测试无效日志级别的验证"""
        config_data = self.valid_config.copy()
        config_data['log_level'] = 'INVALID_LEVEL'

        with self.assertRaises(ValueError):
            TushareConfig(**config_data)

    def test_validate_invalid_interval_order(self):
        """测试无效请求间隔顺序的验证"""
        config_data = self.valid_config.copy()
        config_data['min_request_interval'] = 2.0
        config_data['max_request_interval'] = 1.0

        with self.assertRaises(ValueError):
            TushareConfig(**config_data)

    def test_to_dict(self):
        """测试转换为字典"""
        config = TushareConfig(**self.valid_config)
        config_dict = config.to_dict()

        self.assertIsInstance(config_dict, dict)
        self.assertEqual(config_dict['token'], self.test_token)
        self.assertTrue(config_dict['cache_enabled'])
        self.assertIn('cache_ttl', config_dict)

    def test_update(self):
        """测试更新配置"""
        config = TushareConfig(token=self.test_token)
        updated_config = config.update(cache_ttl=7200, rate_limit=200)

        self.assertEqual(updated_config.cache_ttl, 7200)
        self.assertEqual(updated_config.rate_limit, 200)
        self.assertEqual(updated_config.token, self.test_token)  # 原有配置保持不变

    def test_get_cache_config(self):
        """测试获取缓存配置"""
        config = TushareConfig(**self.valid_config)
        cache_config = config.get_cache_config()

        self.assertEqual(cache_config['enabled'], True)
        self.assertEqual(cache_config['ttl'], 3600)
        self.assertEqual(cache_config['cache_dir'], './test_cache')

    def test_get_api_config(self):
        """测试获取API配置"""
        config = TushareConfig(**self.valid_config)
        api_config = config.get_api_config()

        self.assertEqual(api_config['token'], self.test_token)
        self.assertEqual(api_config['rate_limit'], 120)
        self.assertEqual(api_config['retry_times'], 3)

    def test_get_database_config(self):
        """测试获取数据库配置"""
        config = TushareConfig(**self.valid_config)
        db_config = config.get_database_config()

        self.assertTrue(db_config['save_to_db'])
        self.assertEqual(db_config['batch_size'], 1000)

    def test_get_log_config(self):
        """测试获取日志配置"""
        config = TushareConfig(**self.valid_config)
        log_config = config.get_log_config()

        self.assertEqual(log_config['level'], 'INFO')
        self.assertFalse(log_config['log_requests'])

    def test_str_representation(self):
        """测试字符串表示"""
        config = TushareConfig(token='abcdef123456')
        str_repr = str(config)

        self.assertIn('TushareConfig', str_repr)
        self.assertIn('Enabled' if config.cache_enabled else 'Disabled', str_repr)
        self.assertIn('123456', str_repr)  # 显示token最后几位
        self.assertNotInstanceOf('abcdef123456', str)  # 不显示完整token

    def test_clone(self):
        """测试克隆配置"""
        original_config = TushareConfig(**self.valid_config)
        cloned_config = original_config.clone()

        self.assertEqual(cloned_config.token, original_config.token)
        self.assertEqual(cloned_config.cache_ttl, original_config.cache_ttl)

        # 修改克隆对象不影响原对象
        cloned_config.cache_ttl = 7200
        self.assertEqual(original_config.cache_ttl, 3600)
        self.assertEqual(cloned_config.cache_ttl, 7200)

    def test_get_default_config(self):
        """测试获取默认配置"""
        default_config = TushareConfig.get_default_config()

        self.assertIsInstance(default_config, dict)
        self.assertIn('token', default_config)
        self.assertIn('cache_enabled', default_config)
        self.assertIn('cache_ttl', default_config)

    def test_create_config_template(self):
        """测试创建配置模板"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name

        try:
            result = TushareConfig.create_config_template(temp_file)
            self.assertTrue(result)

            # 验证文件存在且包含注释
            with open(temp_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn('_comment', content)
                self.assertIn('your_tushare_token_here', content)
        finally:
            os.unlink(temp_file)

    def test_environment_variable_type_conversion(self):
        """测试环境变量类型转换"""
        env_vars = {
            'TUSHARE_TOKEN': self.test_token,
            'TUSHARE_CACHE_ENABLED': 'yes',
            'TUSHARE_LOG_REQUESTS': '0',
            'TUSHARE_CACHE_TTL': '7200',
            'TUSHARE_RETRY_TIMES': '5',
            'TUSHARE_PROXY_URL': ''  # 空字符串应该转换为None
        }

        with unittest.mock.patch.dict(os.environ, env_vars):
            config = TushareConfig.from_env()

            self.assertTrue(config.cache_enabled)
            self.assertFalse(config.log_requests)
            self.assertEqual(config.cache_ttl, 7200)
            self.assertEqual(config.retry_times, 5)
            self.assertIsNone(config.proxy_url)


if __name__ == '__main__':
    unittest.main()
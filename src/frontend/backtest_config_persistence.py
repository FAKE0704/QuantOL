from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import os
from src.core.strategy.backtesting import BacktestConfig
from src.support.log.logger import logger

class BacktestConfigPersistence:
    """回测配置持久化管理器

    负责配置文件的保存、加载、删除、导入导出等操作
    支持用户级别的配置隔离
    """

    def __init__(self, base_config_dir: str = "src/support/config/backtest_configs"):
        """初始化配置持久化管理器

        Args:
            base_config_dir: 配置文件存储根目录
        """
        self.base_config_dir = Path(base_config_dir)
        # 确保根目录存在
        self.base_config_dir.mkdir(parents=True, exist_ok=True)

    def _get_user_config_dir(self, username: str) -> Path:
        """获取用户专属配置目录

        Args:
            username: 用户名

        Returns:
            用户配置目录路径
        """
        user_dir = self.base_config_dir / username
        user_dir.mkdir(parents=True, exist_ok=True)

        # 设置目录权限（仅用户本人可访问，Unix系统）
        try:
            os.chmod(user_dir, 0o700)
        except (OSError, AttributeError) as e:
            logger.warning(f"无法设置目录权限: {e}")

        return user_dir

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击

        Args:
            filename: 原始文件名

        Returns:
            清理后的安全文件名
        """
        # 移除危险字符
        dangerous_chars = ['/', '\\', '..', '~', '|', ';', '&', '$', '\0']
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # 限制长度
        return filename[:50].strip()

    def _generate_filename(self, config_name: str) -> str:
        """生成配置文件名

        Args:
            config_name: 配置名称

        Returns:
            配置文件名（含时间戳）
        """
        safe_name = self._sanitize_filename(config_name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{safe_name}_{timestamp}.json"

    def save_config(self, username: str, config_name: str,
                   backtest_config: BacktestConfig,
                   description: str = "") -> str:
        """保存配置到文件

        Args:
            username: 用户名
            config_name: 配置名称
            backtest_config: 回测配置对象
            description: 配置描述

        Returns:
            配置文件路径

        Raises:
            ValueError: 配置验证失败
            OSError: 文件操作失败
        """
        # 验证配置
        self._validate_config_for_save(backtest_config)

        # 生成文件名
        filename = self._generate_filename(config_name)

        # 构建配置数据结构
        config_data = {
            "metadata": {
                "name": config_name,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "username": username,
                "version": "1.0"
            },
            "config": backtest_config.to_dict()
        }

        # 保存到文件
        user_dir = self._get_user_config_dir(username)
        file_path = user_dir / filename

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            # 设置文件权限（仅用户本人可读写）
            try:
                os.chmod(file_path, 0o600)
            except OSError:
                pass

            logger.info(f"配置保存成功: {file_path}")
            return str(file_path)

        except Exception as e:
            logger.error(f"配置保存失败: {e}", exc_info=True)
            raise

    def load_config(self, username: str, config_name: str) -> Optional[Dict[str, Any]]:
        """加载配置文件

        Args:
            username: 用户名
            config_name: 配置名称（可以是文件名或配置名）

        Returns:
            包含元数据和配置的字典，未找到则返回 None
        """
        user_dir = self._get_user_config_dir(username)

        # 尝试直接匹配文件名
        possible_paths = [
            user_dir / config_name,
            user_dir / f"{config_name}.json"
        ]

        # 如果没有找到，尝试按配置名搜索
        for file_path in user_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('metadata', {}).get('name') == config_name:
                        return data
            except (json.JSONDecodeError, KeyError):
                continue

        # 尝试直接加载
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"加载配置文件失败 {path}: {e}")

        return None

    def delete_config(self, username: str, config_name: str) -> bool:
        """删除配置文件

        Args:
            username: 用户名
            config_name: 配置名称

        Returns:
            是否删除成功
        """
        user_dir = self._get_user_config_dir(username)

        # 查找配置文件
        config_path = self._find_config_path(user_dir, config_name)
        if not config_path:
            logger.warning(f"配置文件不存在: {config_name}")
            return False

        try:
            os.remove(config_path)
            logger.info(f"配置文件已删除: {config_path}")
            return True
        except OSError as e:
            logger.error(f"删除配置文件失败: {e}")
            return False

    def list_configs(self, username: str) -> List[Dict[str, Any]]:
        """列出用户所有配置的元数据

        Args:
            username: 用户名

        Returns:
            配置元数据列表
        """
        user_dir = self._get_user_config_dir(username)
        configs = []

        for config_file in user_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    metadata = data.get('metadata', {})

                    # 添加文件路径信息
                    metadata['_filename'] = config_file.name
                    metadata['_filepath'] = str(config_file)

                    configs.append(metadata)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"跳过损坏的配置文件 {config_file.name}: {e}")
                continue

        # 按创建时间倒序排序
        configs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return configs

    def update_config_metadata(self, username: str, config_name: str,
                              description: str = None) -> bool:
        """更新配置元数据

        Args:
            username: 用户名
            config_name: 配置名称
            description: 新的描述（可选）

        Returns:
            是否更新成功
        """
        user_dir = self._get_user_config_dir(username)
        config_path = self._find_config_path(user_dir, config_name)

        if not config_path:
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 更新元数据
            data['metadata']['updated_at'] = datetime.now().isoformat()
            if description is not None:
                data['metadata']['description'] = description

            # 保存
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception as e:
            logger.error(f"更新配置元数据失败: {e}")
            return False

    def export_config(self, username: str, config_name: str,
                     export_path: str) -> bool:
        """导出配置到指定路径

        Args:
            username: 用户名
            config_name: 配置名称
            export_path: 导出路径

        Returns:
            是否导出成功
        """
        config_data = self.load_config(username, config_name)
        if not config_data:
            return False

        # 添加导出元数据
        config_data['metadata']['exported_at'] = datetime.now().isoformat()
        config_data['metadata']['export_type'] = 'user_export'

        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"配置已导出到: {export_path}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False

    def import_config(self, username: str, import_path: str,
                     new_name: str = None) -> bool:
        """从外部路径导入配置

        Args:
            username: 用户名
            import_path: 导入文件路径
            new_name: 新配置名称（可选）

        Returns:
            是否导入成功
        """
        import_file = Path(import_path)
        if not import_file.exists():
            logger.error(f"导入文件不存在: {import_path}")
            return False

        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # 验证格式
            if 'config' not in config_data or 'metadata' not in config_data:
                logger.error("无效的配置文件格式")
                return False

            # 重建 BacktestConfig 对象
            backtest_config = BacktestConfig.from_dict(config_data['config'])

            # 确定配置名称
            config_name = new_name or config_data['metadata'].get('name', 'imported_config')
            description = config_data['metadata'].get('description', '')

            # 保存到用户目录
            self.save_config(username, config_name, backtest_config, description)

            logger.info(f"配置已导入: {config_name}")
            return True

        except Exception as e:
            logger.error(f"导入配置失败: {e}", exc_info=True)
            return False

    def config_exists(self, username: str, config_name: str) -> bool:
        """检查配置是否存在

        Args:
            username: 用户名
            config_name: 配置名称

        Returns:
            配置是否存在
        """
        user_dir = self._get_user_config_dir(username)
        return self._find_config_path(user_dir, config_name) is not None

    def _find_config_path(self, user_dir: Path, config_name: str) -> Optional[Path]:
        """查找配置文件路径

        Args:
            user_dir: 用户配置目录
            config_name: 配置名称

        Returns:
            配置文件路径，未找到则返回 None
        """
        # 直接匹配文件名
        possible_paths = [
            user_dir / config_name,
            user_dir / f"{config_name}.json"
        ]

        for path in possible_paths:
            if path.exists():
                return path

        # 按配置名搜索
        for config_file in user_dir.glob("*.json"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('metadata', {}).get('name') == config_name:
                        return config_file
            except (json.JSONDecodeError, KeyError):
                continue

        return None

    def _validate_config_for_save(self, backtest_config: BacktestConfig) -> None:
        """保存前验证配置

        Args:
            backtest_config: 待验证的配置

        Raises:
            ValueError: 配置验证失败
        """
        # 基本参数检查
        if backtest_config.initial_capital <= 0:
            raise ValueError("初始资金必须大于0")

        if backtest_config.commission_rate < 0:
            raise ValueError("交易佣金不能为负数")

        # 检查交易标的
        symbols = backtest_config.get_symbols()
        if not symbols:
            raise ValueError("未选择交易标的")

        # 日期格式验证（支持多种格式）
        try:
            from datetime import datetime
            date_formats = ["%Y%m%d", "%Y-%m-%d", "%Y/%m/%d"]

            # 验证开始日期
            start_valid = False
            for fmt in date_formats:
                try:
                    datetime.strptime(backtest_config.start_date, fmt)
                    start_valid = True
                    break
                except ValueError:
                    continue

            if not start_valid:
                raise ValueError(f"开始日期格式错误: {backtest_config.start_date}，支持的格式: YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD")

            # 验证结束日期
            end_valid = False
            for fmt in date_formats:
                try:
                    datetime.strptime(backtest_config.end_date, fmt)
                    end_valid = True
                    break
                except ValueError:
                    continue

            if not end_valid:
                raise ValueError(f"结束日期格式错误: {backtest_config.end_date}，支持的格式: YYYYMMDD, YYYY-MM-DD, YYYY/MM/DD")

        except ValueError as e:
            if "日期格式错误" in str(e):
                raise
            raise ValueError(f"日期格式错误: {e}")

        logger.debug("配置验证通过")

"""MindIE-SD 仓库适配器（Ascend/MindIE-SD，包名 mindiesd）。

MindIE-SD 是昇腾标准扩散模型推理引擎，产品代码位于仓库根的 mindiesd/ 包。

覆盖率数据特征（coverage.py 格式，.coveragerc 配置 source = mindiesd）：
- 测试目录：covdata/ 下平铺，tests__ 前缀命名（__ 为路径分隔符）
  函数级用例在脚本名与函数名之间以 -- 连接：
    tests__UT__x__test_foo--test_foo[param]
  文件级用例为纯脚本路径（无 .py 后缀）：
    tests__UT__cache__test_attention_cache
- 每个测试目录下覆盖率文件位于 covdata/ 子目录（pytest-cov 原始文件，
  基类默认 coverage_file_glob = "coverage*" 兼容）
- repo_name = "mindiesd"，product_code_prefix = "mindiesd/"
  覆盖率库中为绝对路径 /home/workspace/MindIE-.../mindiesd/xxx.py，
  按 mindiesd/ 边界剥离（.coveragerc 限定 source = mindiesd，测试文件等
  非 mindiesd/ 路径返回 None 自动排除）
- 源文件解析 source_dir/mindiesd/<rel>（-s 指向含 mindiesd/ 目录的源码根），
  沿用基类默认实现
"""

from fnmatch import fnmatchcase
from pathlib import PurePosixPath

from .base import RepoAdapter


class MindieSdAdapter(RepoAdapter):
    """MindIE-SD（mindiesd）仓库适配器。"""

    repo_name = "mindiesd"
    product_code_prefix = "mindiesd/"
    #: 测试目录均为 tests__ 前缀，无仓库专属多前缀场景（与 vllm 同类）
    test_case_dir_prefix = None

    #: 可纳入 PR 检测的测试根目录（实际布局 tests/UT/... 等）
    TEST_ROOTS = ("tests/",)

    # ------------------------------------------------------------------
    # 覆盖率数据处理
    # ------------------------------------------------------------------
    def is_test_case_dir(self, name: str) -> bool:
        return name.startswith("tests__")

    def normalize_test_name(self, test_name: str) -> str:
        """
        将测试用例目录名转换为标准脚本名：
        - tests__UT__cache__test_attention_cache -> tests/UT/cache/test_attention_cache.py（文件级）
        - tests__UT__x__test_foo--test_foo[param]
          -> tests/UT/x/test_foo.py::test_foo[param]（函数级）
        """
        # 先转换 -- 为 ::（函数级测试标记），再转换 __ 为 /
        result = test_name.replace("--", "::")
        result = result.replace("__", "/")
        if "::" in result:
            # 函数级：脚本段补 .py（目录名中脚本名不含后缀）
            script, _, func = result.partition("::")
            if not script.endswith(".py"):
                script += ".py"
            result = f"{script}::{func}"
        elif not result.endswith(".py"):
            # 文件级且非 .py 后缀则补 .py
            result += ".py"
        return result

    def covered_path_to_rel(self, path: str) -> str | None:
        """覆盖率库路径按 mindiesd/ 边界剥离前缀得到相对路径，否则返回 None。"""
        marker = f"{self.repo_name}/"
        if marker not in path:
            return None
        return path.split(marker)[-1]

    # ------------------------------------------------------------------
    # 测试文件检测（PR 内容检测）
    # ------------------------------------------------------------------
    def is_test_file(self, path: str) -> bool:
        return path.startswith(self.TEST_ROOTS) and fnmatchcase(PurePosixPath(path).name, "test_*.py")

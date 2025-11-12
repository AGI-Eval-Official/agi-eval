from pathlib import PosixPath
import pytest
import json
import logging
import os

from agieval.common.logger import LOG_FILE, logger
from concurrent_log_handler import ConcurrentRotatingFileHandler

def pytest_addoption(parser):
    parser.addoption("--debug_log", action="store_true", help="Output debug logs")

def pytest_runtest_setup(item):
    if item.config.getoption("--debug_log"):    
        os.makedirs("logs", exist_ok=True)
        logger.setLevel(logging.DEBUG)
        file_handler: ConcurrentRotatingFileHandler = ConcurrentRotatingFileHandler(LOG_FILE, encoding="utf-8")
        handler = logging.StreamHandler()

        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(processName)s(%(process)d) - %(caller_filename)s:%(caller_lineno)d - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    

        file_handler.setFormatter(formatter)
        handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(handler)
        

@pytest.fixture
def tmp_multi_choice_dataset(tmp_path: PosixPath):
    dataset = dict(
        examples=[
            dict(
                input="下列关于铁元素生理功能的叙述，错误的是",
                target_scores={
                    "铁可作为光系统工的组分参与光合电子传递": 0.0, 
                    "铁是硝酸还原酶的组分，缺铁时NO3－还原过程受阻": 0.0, 
                    "铁可作为细胞色素的组分参与呼吸电子传递": 0.0, 
                    "铁是叶绿素分子的组分，缺铁时植物会发生缺绿症状": 1.0
                }
            )
        ]
    )
    
    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()

    dataset_file = tmp_path / "multiple_choice.json"
    dataset_file.write_text(json.dumps(dataset, indent=4), encoding="utf-8")
    return str(dataset_file)

@pytest.fixture
def tmp_multi_choice_scenario_state(tmp_path: PosixPath):
    scenario_state = {
        "request_states": [
            {
                "instance": {
                    "input": {"text": "下列关于铁元素生理功能的叙述，错误的是"},
                    "references": [
                        {"output": {"text": "铁可作为光系统工的组分参与光合电子传递"}, "tags": []},
                        {"output": {"text": "铁是硝酸还原酶的组分，缺铁时NO3－还原过程受阻"}, "tags": []},
                        {"output": {"text": "铁可作为细胞色素的组分参与呼吸电子传递"}, "tags": []},
                        {"output": {"text": "铁是叶绿素分子的组分，缺铁时植物会发生缺绿症状"}, "tags": ["correct"]}
                    ],
                    "split": "test",
                    "id": "1"
                },
                "request": {
                    "messages": [
                        {
                            "role": "user",
                            "content": "[Round 0] USER:The following are multiple choice questions about human aging.\n\n下列关于铁元素生理功能的叙述，错误的是\nA. 铁可作为光系统工的组分参与光合电子传递\nB. 铁是硝酸还原酶的组分，缺铁时NO3－还原过程受阻\nC. 铁可作为细胞色素的组分参与呼吸电子传递\nD. 铁是叶绿素分子的组分，缺铁时植物会发生缺绿症状\n\nWhich option is correct and return the correct option. ASSISTANT:"
                        }
                    ],
                    "max_new_tokens": 4096,
                    "temperature": 1,
                    "top_k": 1,
                    "top_p": 1,
                    "repetition_penalty": 1.0,
                    "presence_penalty": 0.0,
                    "model": "",
                    "n_samples": 1,
                    "stop_sequences": [],
                    "target": "D",
                    "original_input_token_num": 0
                },
                "output_mapping": {
                    "A": "铁可作为光系统工的组分参与光合电子传递",
                    "B": "铁是硝酸还原酶的组分，缺铁时NO3－还原过程受阻",
                    "C": "铁可作为细胞色素的组分参与呼吸电子传递",
                    "D": "铁是叶绿素分子的组分，缺铁时植物会发生缺绿症状"
                },
                "multi_turn_requests": [],
                "multi_turn_results": []
            }
        ],
        "extra_configs": {}
    }

    scenario_state_dir = tmp_path / "tmp_multi_choice_dataset"
    scenario_state_dir.mkdir()

    scenario_state_file = scenario_state_dir / "scenario_state.json"
    scenario_state_file.write_text(json.dumps(scenario_state, indent=4), encoding="utf-8")
    return str(scenario_state_file)
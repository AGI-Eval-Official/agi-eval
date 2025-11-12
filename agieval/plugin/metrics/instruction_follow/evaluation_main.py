# coding=utf-8
# Copyright 2024 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Binary of evaluating instruction following. See README.md."""

import collections
import dataclasses
import json
import os
from typing import Dict, Optional, Sequence, Union

# from absl import app
# from absl import flags
# from absl import logging

from agieval.plugin.metrics.instruction_follow.instructions_registry import *


# _INPUT_DATA = flags.DEFINE_string(
#     "input_data", None, "path to input data", required=False
# )

# _INPUT_RESPONSE_DATA = flags.DEFINE_string(
#     "input_response_data", None, "path to input response data", required=False
# )

# _OUTPUT_DIR = flags.DEFINE_string(
#     "output_dir",
#     None,
#     "Output directory for inference and eval results.",
#     required=False,
# )


@dataclasses.dataclass
class InputExample:
    key: int
    instruction_id_list: list[str]
    prompt: str
    kwargs: list[Dict[str, Optional[Union[str, int]]]]


@dataclasses.dataclass
class OutputExample:
    instruction_id_list: list[str]
    # prompt: str
    response: str
    follow_all_instructions: bool
    follow_instruction_list: list[bool]


# def read_prompt_list(input_jsonl_filename):
#   """Read inputs from jsonl."""
#   inputs = []
#   with open(input_jsonl_filename, "r") as f:
#     for l in f:
#       example = json.loads(l)
#       inputs.append(
#           InputExample(key=example["key"],
#                        instruction_id_list=example["instruction_id_list"],
#                        prompt=example["prompt"],
#                        kwargs=example["kwargs"]))
#   return inputs

class InputExamples:
    def __init__(self, key, instruction_id_list,  kwargs):
        self.key = key
        self.instruction_id_list = instruction_id_list
        # self.prompt = prompt
        self.kwargs = kwargs


def read_prompt_list(input_json_filename):
    """Read inputs from JSON."""
    inputs = []
    with open(input_json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)  # 读取整个JSON文件
        for example in data:
            inputs.append(
                InputExamples(key=example["key"],
                              instruction_id_list=example["instruction_id_list"],
                              prompt=example["prompt"],
                              kwargs=example["kwargs"]))
    return inputs


def write_outputs(output_jsonl_filename, outputs):
    """Writes outputs to jsonl."""
    assert outputs
    with open(output_jsonl_filename, "w") as f:
        for o in outputs:
            f.write(
                json.dumps(
                    {
                        attr_name: o.__getattribute__(attr_name)
                        for attr_name in [
                            name for name in dir(o) if not name.startswith("_")
                        ]
                    }
                )
            )
            f.write("\n")


def test_instruction_following_strict(
    inp,
    prompt_to_response,
):
    """Tests response to see if instrutions are followed."""
    response = prompt_to_response[inp.key]
    instruction_list = inp.instruction_id_list
    is_following_list = []

    for index, instruction_id in enumerate(instruction_list):
        instruction_cls = INSTRUCTION_DICT[instruction_id]
        instruction = instruction_cls(instruction_id)

        instruction.build_description(**inp.kwargs[index])
        args = instruction.get_instruction_args()
        # if args and "prompt" in args:
        #   instruction.build_description(prompt=inp.prompt)

        if response.strip() and instruction.check_following(response):
            is_following_list.append(True)
        else:
            is_following_list.append(False)

    return OutputExample(
        instruction_id_list=inp.instruction_id_list,
        # prompt=inp.prompt,
        response=response,
        follow_all_instructions=all(is_following_list),
        follow_instruction_list=is_following_list,
    )


def test_instruction_following_loose(
    inp,
    prompt_to_response,
):
    """Tests response for an upper bound for following instructions."""
    response = prompt_to_response[inp.prompt]
    r = response.split("\n")
    response_remove_first = "\n".join(r[1:]).strip()
    response_remove_last = "\n".join(r[:-1]).strip()
    response_remove_both = "\n".join(r[1:-1]).strip()
    revised_response = response.replace("*", "")
    revised_response_remove_first = response_remove_first.replace("*", "")
    revised_response_remove_last = response_remove_last.replace("*", "")
    revised_response_remove_both = response_remove_both.replace("*", "")
    all_responses = [
        response,
        revised_response,
        response_remove_first,
        response_remove_last,
        response_remove_both,
        revised_response_remove_first,
        revised_response_remove_last,
        revised_response_remove_both,
    ]
    instruction_list = inp.instruction_id_list
    is_following_list = []

    for index, instruction_id in enumerate(instruction_list):
        instruction_cls = INSTRUCTION_DICT[instruction_id]
        instruction = instruction_cls(instruction_id)

        instruction.build_description(**inp.kwargs[index])
        args = instruction.get_instruction_args()
        if args and "prompt" in args:
            instruction.build_description(prompt=inp.prompt)

        is_following = False
        for r in all_responses:
            if r.strip() and instruction.check_following(r):
                is_following = True
                break

        is_following_list.append(is_following)

    return OutputExample(
        instruction_id_list=inp.instruction_id_list,
        prompt=inp.prompt,
        response=response,
        follow_all_instructions=all(is_following_list),
        follow_instruction_list=is_following_list,
    )


def read_prompt_to_response_dict(input_jsonl_filename):
    """Creates dictionary matching prompt and response."""
    return_dict = {}
    with open(input_jsonl_filename, "r") as f:
        for l in f:
            example = json.loads(l)
            return_dict[example["prompt"]] = example["response"]
    return return_dict


def print_report(outputs):
    """Prints a report on accuracy scores."""

    prompt_total = 0
    prompt_correct = 0
    instruction_total = 0
    instruction_correct = 0

    tier0_total = collections.defaultdict(int)
    tier0_correct = collections.defaultdict(int)

    tier1_total = collections.defaultdict(int)
    tier1_correct = collections.defaultdict(int)

    for example in outputs:
        follow_instruction_list = example.follow_instruction_list
        instruction_id_list = example.instruction_id_list

        prompt_total += 1
        if all(follow_instruction_list):
            prompt_correct += 1

        instruction_total += len(instruction_id_list)
        instruction_correct += sum(follow_instruction_list)

        for instruction_id, followed_or_not in zip(
            instruction_id_list, follow_instruction_list
        ):
            instruction_id = instruction_id.split(":")[0]
            tier0_total[instruction_id] += 1
            if followed_or_not:
                tier0_correct[instruction_id] += 1

        for instruction_id, followed_or_not in zip(
            instruction_id_list, follow_instruction_list
        ):
            tier1_total[instruction_id] += 1
            if followed_or_not:
                tier1_correct[instruction_id] += 1

    print(f"prompt-level: {prompt_correct / prompt_total}")
    print(f"instruction-level: {instruction_correct / instruction_total}")
    print()
    for instruction_id in sorted(tier0_total.keys()):
        accuracy = tier0_correct[instruction_id] / tier0_total[instruction_id]
        print(f"{instruction_id} {accuracy}")
    print()
    for instruction_id in sorted(tier1_total.keys()):
        accuracy = tier1_correct[instruction_id] / tier1_total[instruction_id]
        print(f"{instruction_id} {accuracy}")


def main(argv):
    if len(argv) > 1:
        # raise app.UsageError("Too many command-line arguments.")
        raise Exception("Too many command-line arguments.")


if __name__ == "__main__":
    # app.run(main)
    main([])

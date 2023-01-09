from xknx.dpt import *

dpt_dict = {}
for dpt in DPTBase.dpt_class_tree():
    if dpt.value_type is not None:
        dpt_dict[dpt.value_type] = dpt

sort_dict = dict(sorted(dpt_dict.items()))

for dpt in sort_dict.values():
    unit = None
    if dpt.unit is not None:
        unit = f'"{dpt.unit}"'
    print(
        f'("{dpt.value_type}", {dpt.__name__}, {dpt.dpt_main_number}, {dpt.dpt_sub_number}, {unit}),'
    )

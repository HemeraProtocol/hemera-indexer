#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time  2024/8/27 15:14
# @Author  will
# @File  test_namehash.py
# @Brief
import pytest

from indexer.modules.hemera_ens.ens_hash import namehash, get_label, compute_node_label


@pytest.mark.indexer
@pytest.mark.ens
@pytest.mark.serial
def test_namehash():
    demo_name = 'maxga23.eth'
    demo_node = '0xb13b15972f7f65be1ed1313293e4f5e5a006c5420cec802d35dc7e88e7bab183'
    demo_label = '0x1914fcc93afc2b367d581bbae8d17a775b5852b620c32608dd2bdf5d99e89ab5'
    demo_base_node = '93cdeb708b7545dc668eb9280176169d1c33cfd8ed6f04690a0bcc88a93fc4ae'

    name_hash = namehash(demo_name)
    assert name_hash == demo_node
    label = get_label(demo_name.split('.')[0])
    assert label == demo_label
    res = compute_node_label(demo_base_node, demo_label)
    assert res == demo_node
    print('ok!')
    print(get_label('adion'))
    print(get_label('vitalik\x00'))
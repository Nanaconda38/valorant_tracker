def predict_trs_raw(stats: dict) -> float:
    acs = stats.get('acs', 0.0)
    adr = stats.get('adr', 0.0)
    dda = stats.get('dda', 0.0)
    kd = stats.get('kd', 0.0)
    plus_minus = stats.get('plus_minus', 0.0)
    hs_rate = stats.get('hs_rate', 0.0)
    kast_rate = stats.get('kast_rate', 0.0)
    fk_per_round = stats.get('fk_per_round', 0.0)
    fd_per_round = stats.get('fd_per_round', 0.0)
    mk_per_round = stats.get('mk_per_round', 0.0)
    assists_per_round = stats.get('assists_per_round', 0.0)
    kills_per_round = stats.get('kills_per_round', 0.0)
    deaths_per_round = stats.get('deaths_per_round', 0.0)
    won = stats.get('won', 0.0)
    round_diff = stats.get('round_diff', 0.0)
    player_rank_idx = stats.get('player_rank_idx', 0.0)
    avg_rank_idx = stats.get('avg_rank_idx', 0.0)
    rank_delta = stats.get('rank_delta', 0.0)
    log_kill_death = stats.get('log_kill_death', 0.0)
    score = 549.378641

    def tree_0():
        if dda <= -1.500000:
            if log_kill_death <= -0.279808:
                if kast_rate <= 0.680000:
                    return -308.342277
                else:
                    return -163.287732
            else:
                if kast_rate <= 0.680000:
                    return -155.790405
                else:
                    return -37.778641
        else:
            if dda <= 33.500000:
                if kast_rate <= 0.785000:
                    return 53.748632
                else:
                    return 203.358201
            else:
                if kast_rate <= 0.745000:
                    return 175.716597
                else:
                    return 325.036454
    score += 0.100000 * tree_0()

    def tree_1():
        if acs <= 223.500000:
            if log_kill_death <= -0.279808:
                if kast_rate <= 0.535000:
                    return -349.766635
                else:
                    return -205.666565
            else:
                if kast_rate <= 0.725000:
                    return -115.860513
                else:
                    return 21.334353
        else:
            if kast_rate <= 0.745000:
                if adr <= 177.350006:
                    return 50.858634
                else:
                    return 163.492342
            else:
                if dda <= 36.000000:
                    return 185.819973
                else:
                    return 302.471881
    score += 0.100000 * tree_1()

    def tree_2():
        if dda <= -1.500000:
            if acs <= 154.500000:
                if kast_rate <= 0.535000:
                    return -347.639178
                else:
                    return -200.832370
            else:
                if kast_rate <= 0.680000:
                    return -139.844720
                else:
                    return -30.977682
        else:
            if acs <= 242.500000:
                if kast_rate <= 0.635000:
                    return -68.257838
                else:
                    return 72.225644
            else:
                if kast_rate <= 0.735000:
                    return 116.853320
                else:
                    return 248.978194
    score += 0.100000 * tree_2()

    def tree_3():
        if dda <= -2.500000:
            if acs <= 169.500000:
                if kast_rate <= 0.680000:
                    return -230.756678
                else:
                    return -109.116699
            else:
                if kast_rate <= 0.680000:
                    return -105.257315
                else:
                    return -14.893641
        else:
            if dda <= 33.500000:
                if kast_rate <= 0.640000:
                    return -64.201115
                else:
                    return 82.731191
            else:
                if kast_rate <= 0.745000:
                    return 131.674784
                else:
                    return 240.466118
    score += 0.100000 * tree_3()

    def tree_4():
        if acs <= 223.500000:
            if dda <= -31.500000:
                if kast_rate <= 0.680000:
                    return -214.095016
                else:
                    return -91.850696
            else:
                if kast_rate <= 0.755000:
                    return -69.064098
                else:
                    return 46.103771
        else:
            if kast_rate <= 0.785000:
                if dda <= 47.500000:
                    return 59.020728
                else:
                    return 172.893055
            else:
                if adr <= 190.050003:
                    return 172.808205
                else:
                    return 254.800410
    score += 0.100000 * tree_4()

    def tree_5():
        if dda <= 8.500000:
            if log_kill_death <= -0.371209:
                if round_diff <= -0.184265:
                    return -256.882241
                else:
                    return -149.493136
            else:
                if dda <= -19.500000:
                    return -92.559109
                else:
                    return -6.784172
        else:
            if kast_rate <= 0.725000:
                if kast_rate <= 0.630000:
                    return -54.043572
                else:
                    return 74.275593
            else:
                if acs <= 284.000000:
                    return 124.724487
                else:
                    return 213.606258
    score += 0.100000 * tree_5()

    def tree_6():
        if acs <= 223.500000:
            if kast_rate <= 0.680000:
                if dda <= -30.500000:
                    return -176.250432
                else:
                    return -73.991024
            else:
                if adr <= 107.349998:
                    return -87.011046
                else:
                    return 5.674698
        else:
            if kast_rate <= 0.775000:
                if dda <= 47.500000:
                    return 39.850610
                else:
                    return 138.753309
            else:
                if dda <= 48.000000:
                    return 134.576489
                else:
                    return 198.537378
    score += 0.100000 * tree_6()

    def tree_7():
        if dda <= -9.500000:
            if kast_rate <= 0.645000:
                if dda <= -56.000000:
                    return -216.485017
                else:
                    return -126.908587
            else:
                if dda <= -52.500000:
                    return -136.374313
                else:
                    return -36.384447
        else:
            if acs <= 242.500000:
                if kast_rate <= 0.735000:
                    return -14.303262
                else:
                    return 60.627663
            else:
                if kast_rate <= 0.795000:
                    return 88.272486
                else:
                    return 165.687429
    score += 0.100000 * tree_7()

    def tree_8():
        if dda <= 8.500000:
            if acs <= 154.500000:
                if deaths_per_round <= 0.838043:
                    return -106.654107
                else:
                    return -205.086132
            else:
                if kast_rate <= 0.755000:
                    return -49.922744
                else:
                    return 33.201623
        else:
            if dda <= 48.500000:
                if kast_rate <= 0.630000:
                    return -45.389209
                else:
                    return 75.893279
            else:
                if round_diff <= 0.074176:
                    return 117.846008
                else:
                    return 166.411418
    score += 0.100000 * tree_8()

    def tree_9():
        if acs <= 208.500000:
            if kast_rate <= 0.705000:
                if round_diff <= -0.106884:
                    return -146.571873
                else:
                    return -76.846767
            else:
                if kast_rate <= 0.755000:
                    return -40.040210
                else:
                    return 16.350211
        else:
            if kast_rate <= 0.745000:
                if round_diff <= -0.074176:
                    return -7.188268
                else:
                    return 64.668533
            else:
                if acs <= 279.500000:
                    return 86.913083
                else:
                    return 146.551642
    score += 0.100000 * tree_9()

    def tree_10():
        if dda <= -11.500000:
            if kast_rate <= 0.680000:
                if log_kill_death <= -0.786535:
                    return -180.521878
                else:
                    return -90.878215
            else:
                if acs <= 195.500000:
                    return -50.070421
                else:
                    return 7.245934
        else:
            if dda <= 33.500000:
                if kast_rate <= 0.785000:
                    return 9.772509
                else:
                    return 74.983687
            else:
                if kast_rate <= 0.815000:
                    return 78.422097
                else:
                    return 130.668504
    score += 0.100000 * tree_10()

    def tree_11():
        if log_kill_death <= -0.050042:
            if adr <= 122.200001:
                if kast_rate <= 0.535000:
                    return -150.426201
                else:
                    return -69.571259
            else:
                if kast_rate <= 0.600000:
                    return -67.545525
                else:
                    return 1.605128
        else:
            if acs <= 242.500000:
                if kast_rate <= 0.705000:
                    return -19.191670
                else:
                    return 38.393312
            else:
                if kast_rate <= 0.815000:
                    return 62.995727
                else:
                    return 118.050071
    score += 0.100000 * tree_11()

    def tree_12():
        if dda <= -11.500000:
            if kast_rate <= 0.660000:
                if acs <= 153.000000:
                    return -117.780158
                else:
                    return -61.235631
            else:
                if kast_rate <= 0.785000:
                    return -38.724876
                else:
                    return 26.598619
        else:
            if acs <= 252.000000:
                if kast_rate <= 0.735000:
                    return -9.358714
                else:
                    return 41.394977
            else:
                if kast_rate <= 0.720000:
                    return 39.692773
                else:
                    return 99.457116
    score += 0.100000 * tree_12()

    def tree_13():
        if acs <= 198.000000:
            if kast_rate <= 0.745000:
                if round_diff <= -0.269048:
                    return -135.866479
                else:
                    return -57.310862
            else:
                if dda <= -14.500000:
                    return -8.831348
                else:
                    return 22.749877
        else:
            if kast_rate <= 0.725000:
                if round_diff <= -0.074176:
                    return -20.766633
                else:
                    return 36.791489
            else:
                if round_diff <= 0.074176:
                    return 41.464958
                else:
                    return 97.285189
    score += 0.100000 * tree_13()

    def tree_14():
        if acs <= 208.500000:
            if kast_rate <= 0.625000:
                if adr <= 106.050003:
                    return -108.481014
                else:
                    return -61.090819
            else:
                if dda <= -52.500000:
                    return -74.431897
                else:
                    return -12.219526
        else:
            if kast_rate <= 0.725000:
                if round_diff <= -0.106884:
                    return -29.608375
                else:
                    return 27.364076
            else:
                if round_diff <= 0.074176:
                    return 38.298282
                else:
                    return 88.930119
    score += 0.100000 * tree_14()

    def tree_15():
        if dda <= -14.500000:
            if kast_rate <= 0.680000:
                if round_diff <= -0.106884:
                    return -95.891912
                else:
                    return -47.967406
            else:
                if kast_rate <= 0.795000:
                    return -29.484476
                else:
                    return 21.418655
        else:
            if acs <= 279.500000:
                if kast_rate <= 0.765000:
                    return 2.029440
                else:
                    return 42.317311
            else:
                if won <= 0.500000:
                    return 48.004063
                else:
                    return 90.381922
    score += 0.100000 * tree_15()

    def tree_16():
        if adr <= 125.049999:
            if round_diff <= -0.074176:
                if kast_rate <= 0.660000:
                    return -84.216727
                else:
                    return -41.488512
            else:
                if acs <= 127.500000:
                    return -54.918520
                else:
                    return -6.728008
        else:
            if kills_per_round <= 0.937970:
                if round_diff <= -0.002747:
                    return -6.632334
                else:
                    return 31.020555
            else:
                if kast_rate <= 0.885000:
                    return 57.968651
                else:
                    return 123.073009
    score += 0.100000 * tree_16()

    def tree_17():
        if acs <= 208.500000:
            if kast_rate <= 0.625000:
                if round_diff <= 0.080128:
                    return -74.210091
                else:
                    return -27.634130
            else:
                if dda <= -52.500000:
                    return -56.489096
                else:
                    return -8.659186
        else:
            if kast_rate <= 0.785000:
                if round_diff <= 0.000000:
                    return -4.290433
                else:
                    return 37.080973
            else:
                if kast_rate <= 0.885000:
                    return 55.180946
                else:
                    return 108.689921
    score += 0.100000 * tree_17()

    def tree_18():
        if kills_per_round <= 0.844130:
            if acs <= 153.500000:
                if kast_rate <= 0.560000:
                    return -92.249226
                else:
                    return -42.315561
            else:
                if kast_rate <= 0.745000:
                    return -18.544604
                else:
                    return 20.045581
        else:
            if kast_rate <= 0.660000:
                if kast_rate <= 0.625000:
                    return -42.770254
                else:
                    return -2.368172
            else:
                if kast_rate <= 0.860000:
                    return 43.020150
                else:
                    return 79.037011
    score += 0.100000 * tree_18()

    def tree_19():
        if log_kill_death <= -0.055613:
            if dda <= -51.500000:
                if deaths_per_round <= 0.838043:
                    return -42.800414
                else:
                    return -80.629618
            else:
                if kast_rate <= 0.725000:
                    return -27.084539
                else:
                    return 6.051424
        else:
            if log_kill_death <= 0.413339:
                if kast_rate <= 0.660000:
                    return -17.846033
                else:
                    return 23.373958
            else:
                if kast_rate <= 0.885000:
                    return 54.477694
                else:
                    return 104.994238
    score += 0.100000 * tree_19()

    def tree_20():
        if adr <= 125.049999:
            if round_diff <= 0.074176:
                if dda <= -72.500000:
                    return -84.053621
                else:
                    return -40.469056
            else:
                if acs <= 126.000000:
                    return -36.441949
                else:
                    return 0.198033
        else:
            if kd <= 1.550000:
                if round_diff <= -0.184265:
                    return -35.013534
                else:
                    return 16.101651
            else:
                if kast_rate <= 0.885000:
                    return 49.029924
                else:
                    return 94.494815
    score += 0.100000 * tree_20()

    def tree_21():
        if acs <= 198.000000:
            if round_diff <= -0.074176:
                if kast_rate <= 0.760000:
                    return -47.159947
                else:
                    return -0.302471
            else:
                if acs <= 127.500000:
                    return -32.532016
                else:
                    return -0.527619
        else:
            if round_diff <= 0.074176:
                if kast_rate <= 0.725000:
                    return -15.017692
                else:
                    return 17.325176
            else:
                if kast_rate <= 0.840000:
                    return 29.348829
                else:
                    return 68.196440
    score += 0.100000 * tree_21()

    def tree_22():
        if dda <= -14.500000:
            if kast_rate <= 0.560000:
                if acs <= 149.000000:
                    return -71.413158
                else:
                    return -40.263526
            else:
                if kast_rate <= 0.745000:
                    return -23.718430
                else:
                    return 8.967989
        else:
            if adr <= 192.349998:
                if kast_rate <= 0.640000:
                    return -25.890904
                else:
                    return 14.071446
            else:
                if round_diff <= 0.074176:
                    return 24.939598
                else:
                    return 55.081152
    score += 0.100000 * tree_22()

    def tree_23():
        if dda <= 21.500000:
            if round_diff <= -0.184265:
                if adr <= 105.150002:
                    return -63.800145
                else:
                    return -36.367916
            else:
                if kast_rate <= 0.625000:
                    return -29.054481
                else:
                    return -0.796174
        else:
            if kast_rate <= 0.695000:
                if acs <= 311.500000:
                    return -15.618299
                else:
                    return 28.667614
            else:
                if round_diff <= 0.074176:
                    return 18.724966
                else:
                    return 42.664829
    score += 0.100000 * tree_23()

    def tree_24():
        if acs <= 189.500000:
            if round_diff <= 0.074176:
                if acs <= 120.500000:
                    return -63.648818
                else:
                    return -29.852778
            else:
                if assists_per_round <= 0.262014:
                    return -14.565163
                else:
                    return 11.349987
        else:
            if round_diff <= 0.074176:
                if kast_rate <= 0.725000:
                    return -12.172774
                else:
                    return 12.613848
            else:
                if kast_rate <= 0.695000:
                    return 6.105132
                else:
                    return 36.243784
    score += 0.100000 * tree_24()

    def tree_25():
        if kast_rate <= 0.755000:
            if acs <= 189.500000:
                if round_diff <= -0.074176:
                    return -36.588139
                else:
                    return -10.661698
            else:
                if round_diff <= -0.184265:
                    return -28.499680
                else:
                    return 7.187652
        else:
            if kast_rate <= 0.860000:
                if dda <= 55.000000:
                    return 11.882504
                else:
                    return 32.779484
            else:
                if round_diff <= 0.215217:
                    return 37.639938
                else:
                    return 82.975163
    score += 0.100000 * tree_25()

    def tree_26():
        if kills_per_round <= 0.857860:
            if round_diff <= -0.184265:
                if acs <= 143.500000:
                    return -52.377239
                else:
                    return -29.692183
            else:
                if kast_rate <= 0.785000:
                    return -10.159224
                else:
                    return 22.779023
        else:
            if kast_rate <= 0.660000:
                if adr <= 191.750000:
                    return -20.575934
                else:
                    return 6.868153
            else:
                if kast_rate <= 0.860000:
                    return 20.962365
                else:
                    return 41.907670
    score += 0.100000 * tree_26()

    def tree_27():
        if dda <= -26.500000:
            if kast_rate <= 0.745000:
                if round_diff <= -0.106884:
                    return -36.384674
                else:
                    return -16.013710
            else:
                if kast_rate <= 0.820000:
                    return 0.719264
                else:
                    return 28.128947
        else:
            if round_diff <= 0.074176:
                if acs <= 248.500000:
                    return -8.837898
                else:
                    return 9.809462
            else:
                if dda <= 72.000000:
                    return 15.390239
                else:
                    return 46.747028
    score += 0.100000 * tree_27()

    def tree_28():
        if acs <= 193.500000:
            if round_diff <= 0.074176:
                if acs <= 115.000000:
                    return -48.185036
                else:
                    return -20.947075
            else:
                if assists_per_round <= 0.262014:
                    return -10.630537
                else:
                    return 10.463613
        else:
            if round_diff <= 0.074176:
                if round_diff <= -0.184265:
                    return -19.500836
                else:
                    return 5.013759
            else:
                if kast_rate <= 0.840000:
                    return 15.469798
                else:
                    return 39.473247
    score += 0.100000 * tree_28()

    def tree_29():
        if kast_rate <= 0.725000:
            if acs <= 151.500000:
                if round_diff <= 0.334211:
                    return -29.616848
                else:
                    return 12.511972
            else:
                if round_diff <= 0.106884:
                    return -8.911503
                else:
                    return 11.830068
        else:
            if acs <= 287.000000:
                if round_diff <= -0.106884:
                    return -4.922659
                else:
                    return 12.153426
            else:
                if won <= 0.500000:
                    return 15.147502
                else:
                    return 34.228071
    score += 0.100000 * tree_29()

    def tree_30():
        if kast_rate <= 0.625000:
            if kast_rate <= 0.535000:
                if acs <= 145.000000:
                    return -41.925484
                else:
                    return -24.297293
            else:
                if round_diff <= 0.080128:
                    return -18.300964
                else:
                    return -1.661912
        else:
            if dda <= 21.500000:
                if kast_rate <= 0.785000:
                    return -4.974052
                else:
                    return 15.549894
            else:
                if acs <= 285.500000:
                    return 9.165136
                else:
                    return 24.501588
    score += 0.100000 * tree_30()

    def tree_31():
        if acs <= 189.500000:
            if round_diff <= -0.074176:
                if kast_rate <= 0.840000:
                    return -21.079763
                else:
                    return 25.965990
            else:
                if assists_per_round <= 0.262014:
                    return -8.861948
                else:
                    return 6.894866
        else:
            if round_diff <= 0.074176:
                if round_diff <= -0.184265:
                    return -17.043216
                else:
                    return 3.532245
            else:
                if kast_rate <= 0.695000:
                    return 2.125857
                else:
                    return 20.857419
    score += 0.100000 * tree_31()

    def tree_32():
        if kast_rate <= 0.785000:
            if dda <= -34.500000:
                if round_diff <= -0.074176:
                    return -24.505424
                else:
                    return -7.613873
            else:
                if round_diff <= 0.106884:
                    return -4.068639
                else:
                    return 10.665265
        else:
            if round_diff <= -0.334211:
                return -21.956154
            else:
                if kast_rate <= 0.860000:
                    return 12.489618
                else:
                    return 27.292889
    score += 0.100000 * tree_32()

    def tree_33():
        if kast_rate <= 0.625000:
            if kast_rate <= 0.560000:
                if kills_per_round <= 0.384211:
                    return -35.464487
                else:
                    return -20.903664
            else:
                if round_diff <= 0.080128:
                    return -13.489942
                else:
                    return 0.858054
        else:
            if acs <= 282.000000:
                if round_diff <= -0.184265:
                    return -20.969740
                else:
                    return 2.652169
            else:
                if kast_rate <= 0.885000:
                    return 15.204483
                else:
                    return 35.049475
    score += 0.100000 * tree_33()

    def tree_34():
        if kast_rate <= 0.785000:
            if dda <= -56.000000:
                if kills_per_round <= 0.240385:
                    return -38.266884
                else:
                    return -20.016936
            else:
                if round_diff <= 0.106884:
                    return -5.491511
                else:
                    return 8.314225
        else:
            if round_diff <= -0.334211:
                return -17.663565
            else:
                if kast_rate <= 0.860000:
                    return 10.565568
                else:
                    return 22.935051
    score += 0.100000 * tree_34()

    def tree_35():
        if kast_rate <= 0.625000:
            if kast_rate <= 0.560000:
                if fd_per_round <= 0.236695:
                    return -23.161748
                else:
                    return -7.865154
            else:
                if fk_per_round <= 0.113248:
                    return -12.260073
                else:
                    return -0.544030
        else:
            if acs <= 265.500000:
                if round_diff <= -0.184265:
                    return -19.189899
                else:
                    return 1.812576
            else:
                if acs <= 312.000000:
                    return 8.974673
                else:
                    return 21.781067
    score += 0.100000 * tree_35()

    def tree_36():
        if acs <= 189.500000:
            if kast_rate <= 0.745000:
                if acs <= 135.500000:
                    return -18.501701
                else:
                    return -6.872951
            else:
                if deaths_per_round <= 0.780193:
                    return 1.399964
                else:
                    return 27.667699
        else:
            if round_diff <= -0.106884:
                if round_diff <= -0.184265:
                    return -12.049343
                else:
                    return -0.003573
            else:
                if kast_rate <= 0.695000:
                    return -1.312111
                else:
                    return 13.994991
    score += 0.100000 * tree_36()

    def tree_37():
        if kast_rate <= 0.625000:
            if kast_rate <= 0.560000:
                if fd_per_round <= 0.080128:
                    return -27.064763
                else:
                    return -15.318305
            else:
                if round_diff <= 0.080128:
                    return -9.781213
                else:
                    return 2.410047
        else:
            if acs <= 312.000000:
                if round_diff <= -0.106884:
                    return -6.362722
                else:
                    return 4.270429
            else:
                if round_diff <= 0.269048:
                    return 13.696530
                else:
                    return 31.521011
    score += 0.100000 * tree_37()

    def tree_38():
        if adr <= 107.349998:
            if round_diff <= -0.074176:
                if kast_rate <= 0.840000:
                    return -16.062447
                else:
                    return 22.039205
            else:
                if acs <= 151.500000:
                    return -8.306149
                else:
                    return 9.142236
        else:
            if kast_rate <= 0.660000:
                if assists_per_round <= 0.298007:
                    return -8.372335
                else:
                    return 7.523049
            else:
                if round_diff <= -0.106884:
                    return -2.231909
                else:
                    return 9.112180
    score += 0.100000 * tree_38()

    def tree_39():
        if kast_rate <= 0.805000:
            if dda <= -56.000000:
                if hs_rate <= 0.195000:
                    return -18.627296
                else:
                    return -7.720229
            else:
                if round_diff <= 0.106884:
                    return -3.728231
                else:
                    return 5.930917
        else:
            if round_diff <= 0.269048:
                if assists_per_round <= 0.021739:
                    return -33.025722
                else:
                    return 8.765295
            else:
                if kills_per_round <= 1.193498:
                    return 12.110260
                else:
                    return 35.944680
    score += 0.100000 * tree_39()

    def tree_40():
        if acs <= 189.500000:
            if kast_rate <= 0.745000:
                if acs <= 135.500000:
                    return -13.708697
                else:
                    return -5.053408
            else:
                if deaths_per_round <= 0.780193:
                    return 0.540816
                else:
                    return 23.025125
        else:
            if dda <= 72.500000:
                if assists_per_round <= 0.255435:
                    return -0.952350
                else:
                    return 7.891970
            else:
                if round_diff <= 0.269048:
                    return 10.822918
                else:
                    return 30.420060
    score += 0.100000 * tree_40()

    def tree_41():
        if acs <= 189.500000:
            if round_diff <= 0.080128:
                if acs <= 115.000000:
                    return -19.096734
                else:
                    return -6.984323
            else:
                if assists_per_round <= 0.219807:
                    return -6.343720
                else:
                    return 8.860989
        else:
            if round_diff <= -0.184265:
                if hs_rate <= 0.175000:
                    return -3.397706
                else:
                    return -14.484757
            else:
                if adr <= 208.750000:
                    return 3.640557
                else:
                    return 18.477708
    score += 0.100000 * tree_41()

    def tree_42():
        if kast_rate <= 0.805000:
            if kast_rate <= 0.560000:
                if fd_per_round <= 0.236695:
                    return -14.539299
                else:
                    return -1.082670
            else:
                if round_diff <= 0.074176:
                    return -4.358044
                else:
                    return 3.015022
        else:
            if round_diff <= -0.215217:
                if kills_per_round <= 1.146053:
                    return -13.028684
                else:
                    return -3.375147
            else:
                if assists_per_round <= 0.021739:
                    return -29.991970
                else:
                    return 9.667437
    score += 0.100000 * tree_42()

    def tree_43():
        if acs <= 193.500000:
            if round_diff <= 0.074176:
                if kast_rate <= 0.820000:
                    return -8.680827
                else:
                    return 7.826565
            else:
                if assists_per_round <= 0.405882:
                    return -3.150556
                else:
                    return 9.631141
        else:
            if round_diff <= -0.106884:
                if hs_rate <= 0.395000:
                    return -3.985636
                else:
                    return 10.435888
            else:
                if kast_rate <= 0.695000:
                    return -1.336650
                else:
                    return 8.659061
    score += 0.100000 * tree_43()

    def tree_44():
        if adr <= 105.650002:
            if kast_rate <= 0.735000:
                if assists_per_round <= 0.408333:
                    return -10.213581
                else:
                    return 2.504674
            else:
                if fd_per_round <= 0.282609:
                    return 7.498332
                else:
                    return -19.679195
        else:
            if acs <= 312.000000:
                if round_diff <= 0.106884:
                    return -1.194001
                else:
                    return 5.102835
            else:
                if round_diff <= 0.269048:
                    return 8.844313
                else:
                    return 19.584301
    score += 0.100000 * tree_44()

    def tree_45():
        if kast_rate <= 0.585000:
            if fd_per_round <= 0.244048:
                if round_diff <= -0.080128:
                    return -6.637429
                else:
                    return -13.477700
            else:
                if dda <= -38.500000:
                    return -7.064547
                else:
                    return 8.346962
        else:
            if round_diff <= -0.184265:
                if fk_per_round <= 0.153947:
                    return -11.488434
                else:
                    return 1.012466
            else:
                if dda <= 72.500000:
                    return 1.392916
                else:
                    return 12.873855
    score += 0.100000 * tree_45()

    def tree_46():
        if kast_rate <= 0.805000:
            if dda <= -56.000000:
                if hs_rate <= 0.195000:
                    return -12.033857
                else:
                    return -3.654536
            else:
                if round_diff <= 0.106884:
                    return -2.211683
                else:
                    return 3.849502
        else:
            if assists_per_round <= 0.021739:
                return -26.614101
            else:
                if round_diff <= -0.215217:
                    return -7.471529
                else:
                    return 7.322592
    score += 0.100000 * tree_46()

    def tree_47():
        if kast_rate <= 0.860000:
            if dda <= -54.500000:
                if hs_rate <= 0.195000:
                    return -10.830471
                else:
                    return -3.445533
            else:
                if kast_rate <= 0.585000:
                    return -5.902532
                else:
                    return 1.068150
        else:
            if acs <= 345.000000:
                if plus_minus <= 6.500000:
                    return 15.309235
                else:
                    return 3.643617
            else:
                return 27.109175
    score += 0.100000 * tree_47()

    def tree_48():
        if acs <= 312.000000:
            if round_diff <= -0.184265:
                if mk_per_round <= 0.114379:
                    return -6.702677
                else:
                    return -26.156856
            else:
                if kast_rate <= 0.535000:
                    return -11.981739
                else:
                    return 0.725161
        else:
            if deaths_per_round <= 0.737986:
                if kast_rate <= 0.805000:
                    return 7.321460
                else:
                    return 18.005967
            else:
                if deaths_per_round <= 0.836120:
                    return 1.313684
                else:
                    return 9.971885
    score += 0.100000 * tree_48()

    def tree_49():
        if adr <= 105.650002:
            if kast_rate <= 0.735000:
                if log_kill_death <= -0.118194:
                    return -5.479896
                else:
                    return -18.530760
            else:
                if fd_per_round <= 0.282609:
                    return 6.559707
                else:
                    return -15.636651
        else:
            if adr <= 208.750000:
                if assists_per_round <= 0.255435:
                    return -1.188848
                else:
                    return 3.737728
            else:
                if round_diff <= 0.269048:
                    return 6.428006
                else:
                    return 18.241045
    score += 0.100000 * tree_49()

    def tree_50():
        if round_diff <= 0.074176:
            if adr <= 136.900002:
                if fk_per_round <= 0.148352:
                    return -5.340103
                else:
                    return 4.598683
            else:
                if fd_per_round <= 0.042572:
                    return 12.304276
                else:
                    return -1.195646
        else:
            if kast_rate <= 0.535000:
                if assists_per_round <= 0.208333:
                    return -18.648264
                else:
                    return 4.412049
            else:
                if kast_rate <= 0.840000:
                    return 1.895037
                else:
                    return 10.160952
    score += 0.100000 * tree_50()

    def tree_51():
        if acs <= 117.000000:
            if kills_per_round <= 0.371711:
                if log_kill_death <= -0.971495:
                    return -11.957235
                else:
                    return -3.993144
            else:
                return -14.981202
        else:
            if round_diff <= 0.106884:
                if fk_per_round <= 0.240385:
                    return -1.593240
                else:
                    return 7.913957
            else:
                if assists_per_round <= 0.255435:
                    return 1.452680
                else:
                    return 8.841228
    score += 0.100000 * tree_51()

    def tree_52():
        if kast_rate <= 0.860000:
            if acs <= 126.500000:
                if adr <= 92.049999:
                    return -7.987619
                else:
                    return 0.705899
            else:
                if round_diff <= -0.184265:
                    return -5.685938
                else:
                    return 0.706887
        else:
            if plus_minus <= 6.500000:
                if rank_delta <= 14.500000:
                    return 14.870408
                else:
                    return -7.974043
            else:
                if adr <= 213.650002:
                    return 1.311336
                else:
                    return 16.727712
    score += 0.100000 * tree_52()

    def tree_53():
        if dda <= 69.500000:
            if player_rank_idx <= 12.500000:
                if assists_per_round <= 0.318841:
                    return -5.120746
                else:
                    return 4.642758
            else:
                if acs <= 193.500000:
                    return -1.394175
                else:
                    return 3.256798
        else:
            if mk_per_round <= 0.161957:
                if round_diff <= 0.103679:
                    return 5.067090
                else:
                    return 14.387042
            else:
                if acs <= 339.500000:
                    return -5.894071
                else:
                    return 5.901786
    score += 0.100000 * tree_53()

    def tree_54():
        if round_diff <= 0.074176:
            if deaths_per_round <= 0.701993:
                if acs <= 286.500000:
                    return -7.194675
                else:
                    return 7.741036
            else:
                if fd_per_round <= 0.045549:
                    return 5.492014
                else:
                    return -1.877876
        else:
            if kast_rate <= 0.535000:
                if rank_delta <= 9.500000:
                    return -5.106668
                else:
                    return -22.376550
            else:
                if kast_rate <= 0.895000:
                    return 2.016263
                else:
                    return 15.419520
    score += 0.100000 * tree_54()

    def tree_55():
        if dda <= -34.500000:
            if log_kill_death <= -0.243852:
                if fk_per_round <= 0.107692:
                    return -3.291891
                else:
                    return 5.891176
            else:
                if fk_per_round <= 0.101171:
                    return -17.729493
                else:
                    return -6.438763
        else:
            if deaths_per_round <= 0.620192:
                if acs <= 159.000000:
                    return -17.748813
                else:
                    return -1.068787
            else:
                if round_diff <= -0.106884:
                    return -1.651182
                else:
                    return 3.408721
    score += 0.100000 * tree_55()

    def tree_56():
        if acs <= 312.000000:
            if assists_per_round <= 0.255435:
                if player_rank_idx <= 12.500000:
                    return -4.201321
                else:
                    return 0.276322
            else:
                if round_diff <= 0.080128:
                    return -1.033109
                else:
                    return 6.197933
        else:
            if mk_per_round <= 0.184389:
                if deaths_per_round <= 0.718421:
                    return 11.880818
                else:
                    return 4.701558
            else:
                if log_kill_death <= 0.574953:
                    return -8.630448
                else:
                    return 5.336399
    score += 0.100000 * tree_56()

    def tree_57():
        if acs <= 117.000000:
            if kills_per_round <= 0.371711:
                if kills_per_round <= 0.272059:
                    return -9.082622
                else:
                    return -1.995253
            else:
                return -12.315576
        else:
            if round_diff <= 0.106884:
                if deaths_per_round <= 0.660256:
                    return -4.509128
                else:
                    return 0.191180
            else:
                if dda <= -2.500000:
                    return 8.594532
                else:
                    return 0.901037
    score += 0.100000 * tree_57()

    def tree_58():
        if dda <= 69.500000:
            if deaths_per_round <= 0.609903:
                if fk_per_round <= 0.042572:
                    return 2.507250
                else:
                    return -10.241029
            else:
                if dda <= -34.500000:
                    return -2.670491
                else:
                    return 1.199736
        else:
            if plus_minus <= 8.500000:
                return 12.450873
            else:
                if kills_per_round <= 1.161956:
                    return -1.831130
                else:
                    return 6.075821
    score += 0.100000 * tree_58()

    def tree_59():
        if round_diff <= -0.269048:
            if deaths_per_round <= 0.828431:
                if fd_per_round <= 0.077778:
                    return -1.705172
                else:
                    return -11.494875
            else:
                if fd_per_round <= 0.102632:
                    return -7.438540
                else:
                    return 0.450067
        else:
            if dda <= -77.500000:
                if dda <= -89.500000:
                    return -8.989224
                else:
                    return -12.938722
            else:
                if deaths_per_round <= 0.697826:
                    return -1.259073
                else:
                    return 2.173414
    score += 0.100000 * tree_59()

    def tree_60():
        if kast_rate <= 0.860000:
            if hs_rate <= 0.275000:
                if hs_rate <= 0.265000:
                    return -1.216249
                else:
                    return -18.079768
            else:
                if acs <= 153.500000:
                    return -8.406429
                else:
                    return 2.282462
        else:
            if dda <= 34.500000:
                if round_diff <= -0.329923:
                    return -6.441339
                else:
                    return 13.949688
            else:
                if dda <= 80.000000:
                    return 0.278897
                else:
                    return 7.955980
    score += 0.100000 * tree_60()

    def tree_61():
        if dda <= 69.500000:
            if mk_per_round <= 0.219807:
                if deaths_per_round <= 0.707108:
                    return -2.437196
                else:
                    return 0.778385
            else:
                return -26.027203
        else:
            if plus_minus <= 8.500000:
                return 11.278382
            else:
                if kills_per_round <= 1.161956:
                    return -1.789456
                else:
                    return 5.253575
    score += 0.100000 * tree_61()

    def tree_62():
        if kast_rate <= 0.560000:
            if kd <= 0.750000:
                if player_rank_idx <= 20.500000:
                    return -2.398295
                else:
                    return 14.902462
            else:
                if kills_per_round <= 0.673077:
                    return -25.117196
                else:
                    return -7.763827
        else:
            if round_diff <= -0.184265:
                if assists_per_round <= 0.150376:
                    return -0.459767
                else:
                    return -6.753609
            else:
                if acs <= 183.000000:
                    return -1.043178
                else:
                    return 2.039847
    score += 0.100000 * tree_62()

    def tree_63():
        if kast_rate <= 0.860000:
            if deaths_per_round <= 0.479167:
                return -15.646855
            else:
                if dda <= -54.500000:
                    return -3.913674
                else:
                    return 0.163728
        else:
            if dda <= 34.500000:
                if rank_delta <= 14.500000:
                    return 12.431465
                else:
                    return -5.199683
            else:
                if kills_per_round <= 1.230263:
                    return 1.210128
                else:
                    return 11.385344
    score += 0.100000 * tree_63()

    def tree_64():
        if assists_per_round <= 0.233032:
            if player_rank_idx <= 11.500000:
                if deaths_per_round <= 0.493873:
                    return -22.039222
                else:
                    return -3.228006
            else:
                if acs <= 283.000000:
                    return -0.960193
                else:
                    return 5.523896
        else:
            if round_diff <= 0.080128:
                if deaths_per_round <= 0.701993:
                    return -5.496690
                else:
                    return 1.013429
            else:
                if acs <= 240.500000:
                    return 7.600740
                else:
                    return -0.054220
    score += 0.100000 * tree_64()

    def tree_65():
        if acs <= 117.000000:
            if kills_per_round <= 0.371711:
                if kills_per_round <= 0.272059:
                    return -6.604237
                else:
                    return -0.589802
            else:
                return -10.149866
        else:
            if round_diff <= -0.406433:
                if mk_per_round <= 0.199346:
                    return -4.458392
                else:
                    return -22.442694
            else:
                if log_kill_death <= -0.294981:
                    return 3.413113
                else:
                    return -0.123910
    score += 0.100000 * tree_65()

    def tree_66():
        if kast_rate <= 0.860000:
            if deaths_per_round <= 0.609903:
                if fk_per_round <= 0.020833:
                    return 4.155877
                else:
                    return -6.540137
            else:
                if round_diff <= 0.080128:
                    return -0.886166
                else:
                    return 2.210558
        else:
            if dda <= 34.500000:
                if rank_delta <= 14.500000:
                    return 11.108899
                else:
                    return -4.335218
            else:
                if adr <= 203.599998:
                    return 0.085236
                else:
                    return 5.979782
    score += 0.100000 * tree_66()

    def tree_67():
        if kast_rate <= 0.585000:
            if kd <= 0.750000:
                if log_kill_death <= -0.394229:
                    return -3.091304
                else:
                    return 5.386391
            else:
                if kills_per_round <= 0.673077:
                    return -16.600711
                else:
                    return -3.648334
        else:
            if fd_per_round <= 0.306020:
                if round_diff <= -0.106884:
                    return -1.684656
                else:
                    return 1.663530
            else:
                if log_kill_death <= 0.068066:
                    return -9.203073
                else:
                    return -21.073247
    score += 0.100000 * tree_67()

    def tree_68():
        if hs_rate <= 0.275000:
            if kast_rate <= 0.815000:
                if fd_per_round <= 0.037088:
                    return -6.375611
                else:
                    return -0.898722
            else:
                if dda <= -3.500000:
                    return 17.689546
                else:
                    return 0.808779
        else:
            if adr <= 102.000000:
                if dda <= -53.500000:
                    return 3.714638
                else:
                    return -8.967655
            else:
                if fd_per_round <= 0.288462:
                    return 2.467645
                else:
                    return -11.543790
    score += 0.100000 * tree_68()

    def tree_69():
        if assists_per_round <= 0.233032:
            if player_rank_idx <= 11.500000:
                if hs_rate <= 0.085000:
                    return 1.876935
                else:
                    return -3.912367
            else:
                if acs <= 283.000000:
                    return -0.806471
                else:
                    return 4.663078
        else:
            if round_diff <= 0.080128:
                if adr <= 135.049995:
                    return -2.732344
                else:
                    return 2.390392
            else:
                if fd_per_round <= 0.051316:
                    return 0.804189
                else:
                    return 7.609217
    score += 0.100000 * tree_69()

    def tree_70():
        if assists_per_round <= 0.045549:
            if mk_per_round <= 0.116071:
                if deaths_per_round <= 0.680254:
                    return -17.456827
                else:
                    return -2.513060
            else:
                return 4.898004
        else:
            if fk_per_round <= 0.121324:
                if kast_rate <= 0.735000:
                    return -1.801536
                else:
                    return 1.592507
            else:
                if dda <= 1.000000:
                    return 5.241077
                else:
                    return -0.018483
    score += 0.100000 * tree_70()

    def tree_71():
        if acs <= 339.500000:
            if mk_per_round <= 0.219807:
                if assists_per_round <= 0.255435:
                    return -0.966782
                else:
                    return 1.165858
            else:
                return -19.280080
        else:
            if acs <= 364.500000:
                if hs_rate <= 0.255000:
                    return 11.600172
                else:
                    return 7.203189
            else:
                if round_diff <= -0.215217:
                    return -3.798338
                else:
                    return 3.373648
    score += 0.100000 * tree_71()

    def tree_72():
        if hs_rate <= 0.275000:
            if hs_rate <= 0.265000:
                if kast_rate <= 0.815000:
                    return -1.236123
                else:
                    return 2.799257
            else:
                return -11.707779
        else:
            if fd_per_round <= 0.288462:
                if fk_per_round <= 0.240385:
                    return 0.889920
                else:
                    return 8.678564
            else:
                return -10.385556
    score += 0.100000 * tree_72()

    def tree_73():
        if dda <= -78.500000:
            if rank_delta <= 6.500000:
                if hs_rate <= 0.165000:
                    return -6.746723
                else:
                    return -11.237374
            else:
                return 0.505276
        else:
            if log_kill_death <= -0.294981:
                if dda <= -41.500000:
                    return 0.074792
                else:
                    return 6.395107
            else:
                if dda <= -31.500000:
                    return -6.967473
                else:
                    return 0.132722
    score += 0.100000 * tree_73()

    def tree_74():
        if kast_rate <= 0.560000:
            if kd <= 0.750000:
                if player_rank_idx <= 20.500000:
                    return -1.297881
                else:
                    return 12.082741
            else:
                if kills_per_round <= 0.673077:
                    return -20.012821
                else:
                    return -5.508432
        else:
            if round_diff <= -0.184265:
                if hs_rate <= 0.080000:
                    return 4.680147
                else:
                    return -4.084608
            else:
                if deaths_per_round <= 0.609903:
                    return -2.401890
                else:
                    return 1.053873
    score += 0.100000 * tree_74()

    def tree_75():
        if assists_per_round <= 0.045549:
            if mk_per_round <= 0.116071:
                if deaths_per_round <= 0.680254:
                    return -15.465363
                else:
                    return -2.000567
            else:
                return 4.188908
        else:
            if dda <= -34.500000:
                if log_kill_death <= -0.243852:
                    return -0.414907
                else:
                    return -8.865986
            else:
                if plus_minus <= -5.500000:
                    return 8.247817
                else:
                    return 0.404667
    score += 0.100000 * tree_75()

    def tree_76():
        if fd_per_round <= 0.286789:
            if kast_rate <= 0.585000:
                if round_diff <= -0.106884:
                    return 0.527969
                else:
                    return -4.976709
            else:
                if dda <= -1.500000:
                    return 2.036770
                else:
                    return -0.559268
        else:
            if kast_rate <= 0.630000:
                if dda <= -27.000000:
                    return -4.889493
                else:
                    return 6.839533
            else:
                if plus_minus <= 1.500000:
                    return -7.343868
                else:
                    return -16.752940
    score += 0.100000 * tree_76()

    def tree_77():
        if hs_rate <= 0.275000:
            if hs_rate <= 0.265000:
                if kast_rate <= 0.815000:
                    return -1.119816
                else:
                    return 2.510519
            else:
                return -10.553806
        else:
            if adr <= 102.000000:
                if dda <= -53.500000:
                    return 3.152760
                else:
                    return -7.658669
            else:
                if log_kill_death <= -0.055613:
                    return 4.176181
                else:
                    return 0.488865
    score += 0.100000 * tree_77()

    def tree_78():
        if acs <= 339.500000:
            if mk_per_round <= 0.219807:
                if deaths_per_round <= 0.707108:
                    return -1.332935
                else:
                    return 0.582261
            else:
                return -16.705829
        else:
            if acs <= 364.500000:
                if player_rank_idx <= 11.500000:
                    return 10.446188
                else:
                    return 6.133470
            else:
                if kast_rate <= 0.840000:
                    return 2.908504
                else:
                    return -3.342284
    score += 0.100000 * tree_78()

    def tree_79():
        if dda <= 26.500000:
            if dda <= -1.500000:
                if dda <= -26.500000:
                    return -0.984637
                else:
                    return 3.274445
            else:
                if dda <= 10.500000:
                    return -9.925258
                else:
                    return -0.534422
        else:
            if dda <= 31.500000:
                if assists_per_round <= 0.144649:
                    return -0.270049
                else:
                    return 14.684099
            else:
                if kast_rate <= 0.660000:
                    return -6.774115
                else:
                    return 0.646419
    score += 0.100000 * tree_79()

    def tree_80():
        if round_diff <= 0.334211:
            if deaths_per_round <= 0.620192:
                if hs_rate <= 0.205000:
                    return -10.441453
                else:
                    return 0.839601
            else:
                if dda <= -34.500000:
                    return -1.538011
                else:
                    return 0.750462
        else:
            if hs_rate <= 0.180000:
                if player_rank_idx <= 15.500000:
                    return 12.366338
                else:
                    return -0.279851
            else:
                if dda <= 43.500000:
                    return -3.026121
                else:
                    return 4.667480
    score += 0.100000 * tree_80()

    def tree_81():
        if fk_per_round <= 0.233032:
            if round_diff <= 0.080128:
                if fk_per_round <= 0.017857:
                    return -3.453085
                else:
                    return -0.267241
            else:
                if dda <= -3.500000:
                    return 3.322646
                else:
                    return -0.559495
        else:
            if fd_per_round <= 0.308528:
                if rank_delta <= 0.500000:
                    return 9.126584
                else:
                    return 1.003373
            else:
                return -15.206363
    score += 0.100000 * tree_81()

    def tree_82():
        if fd_per_round <= 0.286789:
            if fk_per_round <= 0.233032:
                if assists_per_round <= 0.045549:
                    return -3.921030
                else:
                    return 0.139210
            else:
                if rank_delta <= 0.500000:
                    return 8.213926
                else:
                    return 0.903036
        else:
            if kast_rate <= 0.630000:
                if round_diff <= 0.100932:
                    return -2.824093
                else:
                    return 7.823427
            else:
                if plus_minus <= 1.500000:
                    return -6.363962
                else:
                    return -13.685727
    score += 0.100000 * tree_82()

    def tree_83():
        if hs_rate <= 0.275000:
            if hs_rate <= 0.265000:
                if kast_rate <= 0.815000:
                    return -0.958480
                else:
                    return 2.170490
            else:
                return -9.103373
        else:
            if adr <= 102.000000:
                if dda <= -53.500000:
                    return 3.203618
                else:
                    return -6.686221
            else:
                if hs_rate <= 0.325000:
                    return 3.773739
                else:
                    return 0.265520
    score += 0.100000 * tree_83()

    def tree_84():
        if player_rank_idx <= 5.500000:
            if kast_rate <= 0.520000:
                return 11.581721
            else:
                if fk_per_round <= 0.175000:
                    return -3.211336
                else:
                    return -12.472489
        else:
            if kast_rate <= 0.585000:
                if log_kill_death <= -0.266402:
                    return -0.200815
                else:
                    return -4.879741
            else:
                if dda <= -1.500000:
                    return 1.985836
                else:
                    return -0.595566
    score += 0.100000 * tree_84()

    def tree_85():
        if dda <= 68.500000:
            if deaths_per_round <= 0.609903:
                if mk_per_round <= 0.127717:
                    return -2.275705
                else:
                    return -29.660167
            else:
                if round_diff <= 0.080128:
                    return -0.542514
                else:
                    return 1.445576
        else:
            if plus_minus <= 8.500000:
                return 8.028533
            else:
                if plus_minus <= 10.500000:
                    return -5.206864
                else:
                    return 2.395375
    score += 0.100000 * tree_85()

    def tree_86():
        if round_diff <= -0.406433:
            if kills_per_round <= 1.117647:
                if acs <= 215.000000:
                    return -1.083563
                else:
                    return -11.504204
            else:
                return 9.716006
        else:
            if dda <= -72.000000:
                if log_kill_death <= -0.736653:
                    return -2.372052
                else:
                    return -9.158225
            else:
                if kd <= 0.750000:
                    return 2.506044
                else:
                    return -0.232722
    score += 0.100000 * tree_86()

    def tree_87():
        if dda <= 14.500000:
            if dda <= -1.500000:
                if kast_rate <= 0.800000:
                    return -0.018553
                else:
                    return 7.029460
            else:
                if acs <= 236.500000:
                    return -3.629709
                else:
                    return -11.522771
        else:
            if kast_rate <= 0.745000:
                if kast_rate <= 0.695000:
                    return -1.339040
                else:
                    return 7.553398
            else:
                if kast_rate <= 0.755000:
                    return -12.246123
                else:
                    return -0.344974
    score += 0.100000 * tree_87()

    def tree_88():
        if assists_per_round <= 0.045549:
            if deaths_per_round <= 0.719551:
                if kast_rate <= 0.705000:
                    return -1.071184
                else:
                    return -12.112721
            else:
                if kast_rate <= 0.720000:
                    return -1.816905
                else:
                    return 8.063618
        else:
            if assists_per_round <= 0.085145:
                if rank_delta <= 0.500000:
                    return 13.495953
                else:
                    return 1.269406
            else:
                if fd_per_round <= 0.155870:
                    return 0.404081
                else:
                    return -1.814433
    score += 0.100000 * tree_88()

    def tree_89():
        if kast_rate <= 0.860000:
            if dda <= -1.500000:
                if adr <= 137.250000:
                    return -0.253381
                else:
                    return 5.465150
            else:
                if dda <= 10.500000:
                    return -7.688823
                else:
                    return 0.289110
        else:
            if player_rank_idx <= 22.500000:
                if assists_per_round <= 0.478261:
                    return 4.798854
                else:
                    return -0.954218
            else:
                if adr <= 209.199997:
                    return -4.201416
                else:
                    return 1.698111
    score += 0.100000 * tree_89()

    def tree_90():
        if round_diff <= 0.334211:
            if avg_rank_idx <= 15.500000:
                if assists_per_round <= 0.302174:
                    return -1.616193
                else:
                    return 1.605024
            else:
                if hs_rate <= 0.145000:
                    return -14.566080
                else:
                    return 1.005183
        else:
            if hs_rate <= 0.180000:
                if kd <= 2.200000:
                    return 10.521514
                else:
                    return -0.188300
            else:
                if dda <= 85.500000:
                    return -0.793043
                else:
                    return 10.515397
    score += 0.100000 * tree_90()

    def tree_91():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.535000:
                if round_diff <= -0.106884:
                    return -1.166988
                else:
                    return 0.534420
            else:
                return 10.075299
        else:
            return -5.962211
    score += 0.100000 * tree_91()

    def tree_92():
        if acs <= 339.500000:
            if round_diff <= -0.406433:
                if acs <= 215.000000:
                    return -0.917630
                else:
                    return -9.595125
            else:
                if assists_per_round <= 0.255435:
                    return -0.618905
                else:
                    return 1.047141
        else:
            if acs <= 364.500000:
                if player_rank_idx <= 12.500000:
                    return 7.128478
                else:
                    return 4.055034
            else:
                if kast_rate <= 0.840000:
                    return 2.343984
                else:
                    return -3.039165
    score += 0.100000 * tree_92()

    def tree_93():
        if player_rank_idx <= 5.500000:
            if kast_rate <= 0.520000:
                return 10.776042
            else:
                if hs_rate <= 0.045000:
                    return 4.833092
                else:
                    return -3.845006
        else:
            if hs_rate <= 0.085000:
                if fk_per_round <= 0.063462:
                    return -2.962601
                else:
                    return 6.539292
            else:
                if hs_rate <= 0.145000:
                    return -2.047702
                else:
                    return 0.300103
    score += 0.100000 * tree_93()

    def tree_94():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.535000:
                if round_diff <= -0.106884:
                    return -1.021701
                else:
                    return 0.468993
            else:
                return 9.016347
        else:
            return -5.375761
    score += 0.100000 * tree_94()

    def tree_95():
        if assists_per_round <= 0.045549:
            if deaths_per_round <= 0.719551:
                if round_diff <= 0.106884:
                    return -10.716439
                else:
                    return -0.862709
            else:
                if kast_rate <= 0.720000:
                    return -1.594291
                else:
                    return 7.246095
        else:
            if assists_per_round <= 0.085145:
                if rank_delta <= 0.500000:
                    return 11.984634
                else:
                    return 1.381607
            else:
                if hs_rate <= 0.105000:
                    return 2.205590
                else:
                    return -0.308787
    score += 0.100000 * tree_95()

    def tree_96():
        if dda <= -34.500000:
            if log_kill_death <= -0.243852:
                if deaths_per_round <= 0.639423:
                    return -16.114732
                else:
                    return 0.026384
            else:
                if rank_delta <= 11.500000:
                    return -7.919771
                else:
                    return 4.950923
        else:
            if log_kill_death <= -0.320927:
                if adr <= 114.800003:
                    return 3.153136
                else:
                    return 15.136114
            else:
                if acs <= 193.500000:
                    return -1.934438
                else:
                    return 0.606211
    score += 0.100000 * tree_96()

    def tree_97():
        if round_diff <= 0.334211:
            if deaths_per_round <= 0.633929:
                if fd_per_round <= 0.019231:
                    return -5.589502
                else:
                    return 1.134398
            else:
                if fd_per_round <= 0.045549:
                    return 1.680755
                else:
                    return -0.568829
        else:
            if hs_rate <= 0.180000:
                if deaths_per_round <= 0.470588:
                    return -3.981605
                else:
                    return 8.194168
            else:
                if dda <= 85.500000:
                    return -0.766972
                else:
                    return 9.365653
    score += 0.100000 * tree_97()

    def tree_98():
        if dda <= -50.500000:
            if kast_rate <= 0.660000:
                if fk_per_round <= 0.093478:
                    return -0.886042
                else:
                    return 3.708180
            else:
                if plus_minus <= -7.500000:
                    return -2.622533
                else:
                    return -10.238282
        else:
            if plus_minus <= -5.500000:
                if acs <= 143.500000:
                    return -2.041445
                else:
                    return 6.857159
            else:
                if kast_rate <= 0.535000:
                    return -6.285464
                else:
                    return -0.019051
    score += 0.100000 * tree_98()

    def tree_99():
        if fd_per_round <= 0.286789:
            if fd_per_round <= 0.265050:
                if kast_rate <= 0.585000:
                    return -1.788474
                else:
                    return 0.337993
            else:
                return 6.152088
        else:
            if hs_rate <= 0.230000:
                if plus_minus <= -8.000000:
                    return -2.832301
                else:
                    return 4.577845
            else:
                if player_rank_idx <= 23.000000:
                    return -8.523247
                else:
                    return -1.596281
    score += 0.100000 * tree_99()

    def tree_100():
        if player_rank_idx <= 5.500000:
            if deaths_per_round <= 0.875000:
                if hs_rate <= 0.045000:
                    return 3.621677
                else:
                    return -3.369427
            else:
                return 9.127425
        else:
            if kd <= 0.750000:
                if dda <= -40.500000:
                    return -0.035597
                else:
                    return 4.589245
            else:
                if dda <= -26.500000:
                    return -3.697387
                else:
                    return 0.300565
    score += 0.100000 * tree_100()

    def tree_101():
        if kast_rate <= 0.860000:
            if dda <= -1.500000:
                if adr <= 137.250000:
                    return -0.157076
                else:
                    return 4.909969
            else:
                if dda <= 10.500000:
                    return -6.728611
                else:
                    return 0.183703
        else:
            if dda <= 34.500000:
                if assists_per_round <= 0.489770:
                    return 7.159036
                else:
                    return -2.620679
            else:
                if player_rank_idx <= 21.000000:
                    return 2.625440
                else:
                    return -1.976861
    score += 0.100000 * tree_101()

    def tree_102():
        if round_diff <= 0.334211:
            if avg_rank_idx <= 15.500000:
                if assists_per_round <= 0.302174:
                    return -1.335258
                else:
                    return 1.269440
            else:
                if hs_rate <= 0.145000:
                    return -12.445029
                else:
                    return 0.869687
        else:
            if fk_per_round <= 0.057190:
                if hs_rate <= 0.225000:
                    return 9.960630
                else:
                    return 2.348716
            else:
                if acs <= 303.000000:
                    return -1.305898
                else:
                    return 4.179407
    score += 0.100000 * tree_102()

    def tree_103():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.535000:
                if hs_rate <= 0.455000:
                    return 0.107463
                else:
                    return -3.594337
            else:
                return 7.938147
        else:
            return -4.705810
    score += 0.100000 * tree_103()

    def tree_104():
        if acs <= 339.500000:
            if adr <= 197.800003:
                if adr <= 194.449997:
                    return -0.094133
                else:
                    return 7.522865
            else:
                if round_diff <= 0.334211:
                    return -4.355676
                else:
                    return 2.799450
        else:
            if acs <= 364.500000:
                if plus_minus <= 8.500000:
                    return 7.848827
                else:
                    return 3.939895
            else:
                if fd_per_round <= 0.025000:
                    return -4.720219
                else:
                    return 1.655443
    score += 0.100000 * tree_104()

    def tree_105():
        if hs_rate <= 0.275000:
            if hs_rate <= 0.265000:
                if kast_rate <= 0.815000:
                    return -0.637113
                else:
                    return 1.636727
            else:
                return -7.854127
        else:
            if acs <= 151.500000:
                if deaths_per_round <= 0.804348:
                    return -5.183497
                else:
                    return 3.792466
            else:
                if kills_per_round <= 0.839744:
                    return 2.463272
                else:
                    return -0.610204
    score += 0.100000 * tree_105()

    def tree_106():
        if dda <= 68.500000:
            if plus_minus <= 6.500000:
                if dda <= 26.500000:
                    return -0.254929
                else:
                    return 2.207265
            else:
                if fd_per_round <= 0.114907:
                    return -5.082733
                else:
                    return 3.106363
        else:
            if rank_delta <= 12.500000:
                if kast_rate <= 0.905000:
                    return 3.093233
                else:
                    return -4.125953
            else:
                if assists_per_round <= 0.178947:
                    return 0.758272
                else:
                    return -6.737077
    score += 0.100000 * tree_106()

    def tree_107():
        if acs <= 221.500000:
            if acs <= 220.500000:
                if adr <= 140.050003:
                    return -0.082436
                else:
                    return 6.803921
            else:
                return 20.070114
        else:
            if kast_rate <= 0.675000:
                if deaths_per_round <= 0.889676:
                    return -6.496662
                else:
                    return 4.824585
            else:
                if kast_rate <= 0.745000:
                    return 3.588666
                else:
                    return -1.662981
    score += 0.100000 * tree_107()

    def tree_108():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.017857:
                if fd_per_round <= 0.040970:
                    return -8.516274
                else:
                    return -1.376661
            else:
                if assists_per_round <= 0.419872:
                    return 0.394226
                else:
                    return -3.146682
        else:
            if acs <= 243.500000:
                if assists_per_round <= 0.219807:
                    return -0.115456
                else:
                    return 5.436748
            else:
                if dda <= 9.500000:
                    return -18.374070
                else:
                    return -0.160458
    score += 0.100000 * tree_108()

    def tree_109():
        if kast_rate <= 0.860000:
            if acs <= 221.500000:
                if acs <= 220.500000:
                    return 0.190651
                else:
                    return 18.023680
            else:
                if kast_rate <= 0.745000:
                    return 0.563601
                else:
                    return -2.998593
        else:
            if player_rank_idx <= 22.500000:
                if assists_per_round <= 0.478261:
                    return 3.652699
                else:
                    return -0.505893
            else:
                if assists_per_round <= 0.303512:
                    return -3.600050
                else:
                    return 0.081462
    score += 0.100000 * tree_109()

    def tree_110():
        if assists_per_round <= 0.045549:
            if fk_per_round <= 0.040064:
                return 8.820924
            else:
                if rank_delta <= 1.500000:
                    return -4.880714
                else:
                    return 0.683756
        else:
            if assists_per_round <= 0.085145:
                if rank_delta <= 0.500000:
                    return 10.354319
                else:
                    return 1.366655
            else:
                if hs_rate <= 0.595000:
                    return 0.019604
                else:
                    return -8.152984
    score += 0.100000 * tree_110()

    def tree_111():
        if dda <= 68.500000:
            if dda <= 33.500000:
                if dda <= 26.500000:
                    return -0.309821
                else:
                    return 6.537854
            else:
                if fd_per_round <= 0.228758:
                    return -2.385543
                else:
                    return 4.949426
        else:
            if rank_delta <= 12.500000:
                if plus_minus <= 9.000000:
                    return 5.441744
                else:
                    return 1.972207
            else:
                if assists_per_round <= 0.178947:
                    return 0.882519
                else:
                    return -5.610861
    score += 0.100000 * tree_111()

    def tree_112():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.040064:
                if fd_per_round <= 0.040970:
                    return -4.443602
                else:
                    return -0.818644
            else:
                if mk_per_round <= 0.042572:
                    return 1.416300
                else:
                    return -0.925865
        else:
            if adr <= 150.700005:
                if adr <= 126.250000:
                    return 0.387422
                else:
                    return 7.174087
            else:
                if kast_rate <= 0.660000:
                    return -9.959932
                else:
                    return 0.449816
    score += 0.100000 * tree_112()

    def tree_113():
        if acs <= 263.500000:
            if acs <= 250.500000:
                if round_diff <= 0.106884:
                    return -0.454565
                else:
                    return 1.783399
            else:
                if rank_delta <= 7.000000:
                    return -8.672663
                else:
                    return 3.884577
        else:
            if adr <= 166.050003:
                return 16.862263
            else:
                if kast_rate <= 0.745000:
                    return 2.789513
                else:
                    return -0.377710
    score += 0.100000 * tree_113()

    def tree_114():
        if kd <= 0.750000:
            if dda <= -50.500000:
                if kast_rate <= 0.660000:
                    return 0.278083
                else:
                    return -3.638641
            else:
                if rank_delta <= 7.500000:
                    return 4.259883
                else:
                    return -1.863649
        else:
            if plus_minus <= -4.500000:
                if avg_rank_idx <= 21.000000:
                    return -16.719462
                else:
                    return -2.321661
            else:
                if acs <= 180.500000:
                    return -2.535666
                else:
                    return 0.458290
    score += 0.100000 * tree_114()

    def tree_115():
        if kast_rate <= 0.860000:
            if log_kill_death <= -0.050042:
                if adr <= 140.050003:
                    return -0.175455
                else:
                    return 5.267290
            else:
                if deaths_per_round <= 0.734950:
                    return 0.236358
                else:
                    return -2.681165
        else:
            if dda <= 34.500000:
                if round_diff <= -0.329923:
                    return -1.974299
                else:
                    return 5.931204
            else:
                if log_kill_death <= 0.444060:
                    return -1.725739
                else:
                    return 1.870329
    score += 0.100000 * tree_115()

    def tree_116():
        if player_rank_idx <= 5.500000:
            if kast_rate <= 0.520000:
                return 8.326531
            else:
                if hs_rate <= 0.045000:
                    return 3.371358
                else:
                    return -2.938787
        else:
            if hs_rate <= 0.085000:
                if fk_per_round <= 0.063462:
                    return -2.304273
                else:
                    return 5.017476
            else:
                if hs_rate <= 0.145000:
                    return -1.755957
                else:
                    return 0.258665
    score += 0.100000 * tree_116()

    def tree_117():
        if acs <= 339.500000:
            if mk_per_round <= 0.219807:
                if adr <= 197.800003:
                    return 0.071673
                else:
                    return -2.108895
            else:
                return -10.741044
        else:
            if adr <= 266.099991:
                if plus_minus <= 8.500000:
                    return 5.965433
                else:
                    return 2.524587
            else:
                return -0.037070
    score += 0.100000 * tree_117()

    def tree_118():
        if kast_rate <= 0.585000:
            if round_diff <= -0.080128:
                if dda <= 29.000000:
                    return 0.559418
                else:
                    return 10.462477
            else:
                if fd_per_round <= 0.229167:
                    return -4.950779
                else:
                    return 1.983927
        else:
            if round_diff <= -0.106884:
                if fd_per_round <= 0.093478:
                    return 0.241888
                else:
                    return -3.344820
            else:
                if round_diff <= -0.080128:
                    return 3.668764
                else:
                    return 0.399730
    score += 0.100000 * tree_118()

    def tree_119():
        if kd <= 0.750000:
            if dda <= -50.500000:
                if kast_rate <= 0.660000:
                    return 0.281799
                else:
                    return -3.168722
            else:
                if rank_delta <= 7.500000:
                    return 3.822163
                else:
                    return -1.840765
        else:
            if dda <= -26.500000:
                if adr <= 107.000000:
                    return -7.999397
                else:
                    return -1.398479
            else:
                if plus_minus <= -4.500000:
                    return -12.010142
                else:
                    return 0.260298
    score += 0.100000 * tree_119()

    def tree_120():
        if dda <= -4.500000:
            if kast_rate <= 0.820000:
                if kast_rate <= 0.680000:
                    return 0.996232
                else:
                    return -1.258870
            else:
                if adr <= 139.750000:
                    return 4.705440
                else:
                    return 23.883797
        else:
            if dda <= 10.500000:
                if hs_rate <= 0.345000:
                    return -5.386601
                else:
                    return 8.525226
            else:
                if kills_per_round <= 0.568323:
                    return -11.285604
                else:
                    return 0.548118
    score += 0.100000 * tree_120()

    def tree_121():
        if kast_rate <= 0.585000:
            if round_diff <= -0.080128:
                if hs_rate <= 0.390000:
                    return 0.365004
                else:
                    return 9.335388
            else:
                if fd_per_round <= 0.229167:
                    return -4.508913
                else:
                    return 1.392204
        else:
            if round_diff <= -0.106884:
                if assists_per_round <= 0.097619:
                    return -5.351126
                else:
                    return -0.351927
            else:
                if fd_per_round <= 0.037088:
                    return -1.004750
                else:
                    return 1.120745
    score += 0.100000 * tree_121()

    def tree_122():
        if player_rank_idx <= 5.500000:
            if deaths_per_round <= 0.875000:
                if dda <= -59.500000:
                    return -4.713473
                else:
                    return -1.587846
            else:
                return 6.912429
        else:
            if log_kill_death <= -0.050042:
                if fk_per_round <= 0.040064:
                    return -1.751862
                else:
                    return 1.760697
            else:
                if kast_rate <= 0.660000:
                    return -3.784624
                else:
                    return 0.144457
    score += 0.100000 * tree_122()

    def tree_123():
        if acs <= 263.500000:
            if acs <= 250.500000:
                if round_diff <= 0.106884:
                    return -0.376431
                else:
                    return 1.573538
            else:
                if fk_per_round <= 0.211957:
                    return -7.732355
                else:
                    return 3.411014
        else:
            if adr <= 166.050003:
                return 15.240215
            else:
                if kast_rate <= 0.745000:
                    return 2.580686
                else:
                    return -0.474146
    score += 0.100000 * tree_123()

    def tree_124():
        if fd_per_round <= 0.286789:
            if kast_rate <= 0.585000:
                if round_diff <= -0.080128:
                    return 0.742175
                else:
                    return -3.396725
            else:
                if avg_rank_idx <= 10.500000:
                    return -0.392904
                else:
                    return 1.109882
        else:
            if hs_rate <= 0.230000:
                if log_kill_death <= -0.487857:
                    return -1.844846
                else:
                    return 2.661204
            else:
                if assists_per_round <= 0.173913:
                    return -7.466149
                else:
                    return -3.628321
    score += 0.100000 * tree_124()

    def tree_125():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.510000:
                if kast_rate <= 0.845000:
                    return -0.171678
                else:
                    return 1.412413
            else:
                return 5.917155
        else:
            return -3.752911
    score += 0.100000 * tree_125()

    def tree_126():
        if acs <= 221.500000:
            if adr <= 135.449997:
                if adr <= 133.650002:
                    return 0.102153
                else:
                    return -11.668282
            else:
                if fd_per_round <= 0.048611:
                    return 9.823493
                else:
                    return 2.580983
        else:
            if kast_rate <= 0.675000:
                if deaths_per_round <= 0.889676:
                    return -4.977790
                else:
                    return 3.962458
            else:
                if kast_rate <= 0.745000:
                    return 2.542707
                else:
                    return -1.241286
    score += 0.100000 * tree_126()

    def tree_127():
        if dda <= 71.500000:
            if plus_minus <= 6.500000:
                if kills_per_round <= 1.019231:
                    return -0.036583
                else:
                    return 3.991288
            else:
                if adr <= 164.450005:
                    return -8.850516
                else:
                    return -0.862808
        else:
            if player_rank_idx <= 12.500000:
                if acs <= 362.500000:
                    return 4.040695
                else:
                    return 1.653886
            else:
                if fk_per_round <= 0.065217:
                    return 2.492221
                else:
                    return -0.263675
    score += 0.100000 * tree_127()

    def tree_128():
        if round_diff <= -0.269048:
            if assists_per_round <= 0.171569:
                if mk_per_round <= 0.199346:
                    return 1.509994
                else:
                    return -4.076469
            else:
                if plus_minus <= -8.500000:
                    return 2.073289
                else:
                    return -4.722439
        else:
            if dda <= -72.000000:
                if hs_rate <= 0.225000:
                    return -4.214592
                else:
                    return 2.670722
            else:
                if log_kill_death <= -0.377092:
                    return 2.304474
                else:
                    return -0.040086
    score += 0.100000 * tree_128()

    def tree_129():
        if fk_per_round <= 0.121324:
            if kast_rate <= 0.735000:
                if mk_per_round <= 0.067873:
                    return -0.220576
                else:
                    return -3.732285
            else:
                if assists_per_round <= 0.327381:
                    return 2.395916
                else:
                    return -1.425394
        else:
            if kast_rate <= 0.745000:
                if fd_per_round <= 0.175192:
                    return 3.326986
                else:
                    return -1.517054
            else:
                if adr <= 127.700001:
                    return 6.814666
                else:
                    return -1.819708
    score += 0.100000 * tree_129()

    def tree_130():
        if acs <= 339.500000:
            if acs <= 221.500000:
                if acs <= 210.500000:
                    return -0.118930
                else:
                    return 5.348679
            else:
                if dda <= 14.500000:
                    return -3.102632
                else:
                    return 0.099945
        else:
            if plus_minus <= 11.500000:
                return 3.375794
            else:
                if plus_minus <= 13.500000:
                    return -1.008107
                else:
                    return 1.998471
    score += 0.100000 * tree_130()

    def tree_131():
        if deaths_per_round <= 0.906522:
            if deaths_per_round <= 0.763305:
                if deaths_per_round <= 0.707108:
                    return -0.429275
                else:
                    return 1.495038
            else:
                if fd_per_round <= 0.116516:
                    return -1.901520
                else:
                    return 0.470037
        else:
            if log_kill_death <= -0.195863:
                if player_rank_idx <= 21.500000:
                    return -1.004898
                else:
                    return 3.796833
            else:
                if fd_per_round <= 0.085145:
                    return 2.750013
                else:
                    return 7.260429
    score += 0.100000 * tree_131()

    def tree_132():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.510000:
                if kast_rate <= 0.845000:
                    return -0.168848
                else:
                    return 1.447083
            else:
                return 5.081921
        else:
            return -3.586897
    score += 0.100000 * tree_132()

    def tree_133():
        if deaths_per_round <= 0.893797:
            if kast_rate <= 0.510000:
                if assists_per_round <= 0.120192:
                    return 1.274412
                else:
                    return -5.367795
            else:
                if acs <= 221.500000:
                    return 0.520926
                else:
                    return -0.592082
        else:
            if dda <= -49.500000:
                if fk_per_round <= 0.051316:
                    return -4.362745
                else:
                    return 0.339633
            else:
                if hs_rate <= 0.275000:
                    return 1.711868
                else:
                    return 4.203268
    score += 0.100000 * tree_133()

    def tree_134():
        if acs <= 339.500000:
            if adr <= 197.800003:
                if adr <= 194.449997:
                    return -0.088704
                else:
                    return 5.758218
            else:
                if acs <= 282.500000:
                    return -12.497686
                else:
                    return -1.303419
        else:
            if fk_per_round <= 0.087104:
                return 3.441247
            else:
                if assists_per_round <= 0.284615:
                    return 1.658675
                else:
                    return -1.550462
    score += 0.100000 * tree_134()

    def tree_135():
        if acs <= 124.500000:
            if kills_per_round <= 0.371711:
                if kills_per_round <= 0.292892:
                    return -1.873810
                else:
                    return 1.391941
            else:
                if rank_delta <= -0.500000:
                    return 0.910368
                else:
                    return -4.936002
        else:
            if log_kill_death <= -0.279808:
                if rank_delta <= 7.500000:
                    return 2.753952
                else:
                    return -1.385491
            else:
                if dda <= -26.500000:
                    return -2.548417
                else:
                    return 0.148514
    score += 0.100000 * tree_135()

    def tree_136():
        if fd_per_round <= 0.212862:
            if fk_per_round <= 0.233032:
                if log_kill_death <= -0.050042:
                    return 0.615416
                else:
                    return -0.664338
            else:
                if dda <= 26.500000:
                    return 6.068321
                else:
                    return 0.146454
        else:
            if plus_minus <= 5.500000:
                if deaths_per_round <= 0.780193:
                    return -4.122395
                else:
                    return -0.581642
            else:
                return 5.007882
    score += 0.100000 * tree_136()

    def tree_137():
        if dda <= 26.500000:
            if log_kill_death <= 0.327463:
                if deaths_per_round <= 0.568323:
                    return -5.201514
                else:
                    return 0.031175
            else:
                return -8.597496
        else:
            if dda <= 31.500000:
                if assists_per_round <= 0.144649:
                    return -0.251041
                else:
                    return 8.808262
            else:
                if kills_per_round <= 0.693980:
                    return 8.017294
                else:
                    return -0.507711
    score += 0.100000 * tree_137()

    def tree_138():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.017857:
                if fd_per_round <= 0.040970:
                    return -6.202745
                else:
                    return -1.103878
            else:
                if assists_per_round <= 0.419872:
                    return 0.324581
                else:
                    return -2.378829
        else:
            if hs_rate <= 0.135000:
                if adr <= 168.800003:
                    return 5.063478
                else:
                    return 0.033706
            else:
                if acs <= 243.500000:
                    return 1.080901
                else:
                    return -1.021037
    score += 0.100000 * tree_138()

    def tree_139():
        if acs <= 265.500000:
            if acs <= 250.500000:
                if fd_per_round <= 0.093478:
                    return 0.754387
                else:
                    return -0.842263
            else:
                if acs <= 254.500000:
                    return -12.080258
                else:
                    return -1.736545
        else:
            if kast_rate <= 0.745000:
                if rank_delta <= 9.500000:
                    return 5.806438
                else:
                    return -0.643258
            else:
                if kast_rate <= 0.810000:
                    return -3.957245
                else:
                    return 0.777401
    score += 0.100000 * tree_139()

    def tree_140():
        if dda <= 71.500000:
            if plus_minus <= 6.500000:
                if dda <= 26.500000:
                    return -0.206850
                else:
                    return 1.484313
            else:
                if adr <= 164.450005:
                    return -7.042234
                else:
                    return -0.703570
        else:
            if hs_rate <= 0.365000:
                if deaths_per_round <= 0.688259:
                    return 2.801137
                else:
                    return 0.782156
            else:
                if fk_per_round <= 0.136646:
                    return -2.726967
                else:
                    return 1.988886
    score += 0.100000 * tree_140()

    def tree_141():
        if player_rank_idx <= 5.500000:
            if kast_rate <= 0.520000:
                return 5.704654
            else:
                if kast_rate <= 0.770000:
                    return -2.593781
                else:
                    return 0.185613
        else:
            if player_rank_idx <= 7.500000:
                if assists_per_round <= 0.326087:
                    return -0.036784
                else:
                    return 5.232413
            else:
                if acs <= 183.000000:
                    return -0.664128
                else:
                    return 0.304301
    score += 0.100000 * tree_141()

    def tree_142():
        if dda <= -4.500000:
            if dda <= -8.500000:
                if assists_per_round <= 0.091097:
                    return 2.717393
                else:
                    return -0.280838
            else:
                if hs_rate <= 0.245000:
                    return 13.975495
                else:
                    return 0.268613
        else:
            if dda <= 10.500000:
                if hs_rate <= 0.345000:
                    return -4.274189
                else:
                    return 6.750304
            else:
                if kills_per_round <= 0.568323:
                    return -9.061834
                else:
                    return 0.405005
    score += 0.100000 * tree_142()

    def tree_143():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.510000:
                if hs_rate <= 0.455000:
                    return 0.063905
                else:
                    return -2.568883
            else:
                return 4.242302
        else:
            return -3.399167
    score += 0.100000 * tree_143()

    def tree_144():
        if round_diff <= 0.334211:
            if log_kill_death <= -0.050042:
                if fk_per_round <= 0.040064:
                    return -1.411949
                else:
                    return 1.193699
            else:
                if deaths_per_round <= 0.734950:
                    return 0.284295
                else:
                    return -1.874067
        else:
            if hs_rate <= 0.180000:
                if fk_per_round <= 0.057190:
                    return 6.284612
                else:
                    return 1.660072
            else:
                if acs <= 303.000000:
                    return -0.657917
                else:
                    return 3.074880
    score += 0.100000 * tree_144()

    def tree_145():
        if log_kill_death <= -0.279808:
            if dda <= -40.500000:
                if kast_rate <= 0.760000:
                    return -0.734354
                else:
                    return 5.498804
            else:
                if round_diff <= -0.269048:
                    return -1.429220
                else:
                    return 3.954729
        else:
            if plus_minus <= -4.500000:
                if avg_rank_idx <= 21.000000:
                    return -12.412397
                else:
                    return -1.334105
            else:
                if acs <= 160.500000:
                    return -3.636023
                else:
                    return 0.115547
    score += 0.100000 * tree_145()

    def tree_146():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.017857:
                if fd_per_round <= 0.040970:
                    return -5.362317
                else:
                    return -0.730681
            else:
                if deaths_per_round <= 0.763305:
                    return 0.680788
                else:
                    return -0.723854
        else:
            if assists_per_round <= 0.255435:
                if fd_per_round <= 0.183473:
                    return 0.168363
                else:
                    return -2.987842
            else:
                if adr <= 149.850006:
                    return 3.665245
                else:
                    return -0.033741
    score += 0.100000 * tree_146()

    def tree_147():
        if log_kill_death <= -0.050042:
            if adr <= 140.050003:
                if adr <= 131.650002:
                    return 0.259169
                else:
                    return -3.058043
            else:
                if fd_per_round <= 0.042572:
                    return 9.221152
                else:
                    return 1.918078
        else:
            if kast_rate <= 0.660000:
                if fd_per_round <= 0.019231:
                    return -13.587311
                else:
                    return -2.100804
            else:
                if kast_rate <= 0.745000:
                    return 1.356279
                else:
                    return -0.815970
    score += 0.100000 * tree_147()

    def tree_148():
        if adr <= 208.750000:
            if adr <= 205.699997:
                if acs <= 221.500000:
                    return 0.298879
                else:
                    return -0.517646
            else:
                return -5.538510
        else:
            if log_kill_death <= 0.460994:
                if kd <= 1.300000:
                    return 1.171876
                else:
                    return 3.796099
            else:
                if fk_per_round <= 0.224080:
                    return 0.149967
                else:
                    return 1.770408
    score += 0.100000 * tree_148()

    def tree_149():
        if kast_rate <= 0.860000:
            if acs <= 221.500000:
                if acs <= 220.500000:
                    return 0.120906
                else:
                    return 11.711020
            else:
                if acs <= 263.500000:
                    return -1.731056
                else:
                    return 0.663297
        else:
            if dda <= 34.500000:
                if player_rank_idx <= 11.500000:
                    return 8.110523
                else:
                    return 2.822125
            else:
                if avg_rank_idx <= 21.000000:
                    return 1.469629
                else:
                    return -1.018894
    score += 0.100000 * tree_149()

    def tree_150():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.184524:
                if fk_per_round <= 0.170290:
                    return -0.278277
                else:
                    return -5.614123
            else:
                if adr <= 179.150002:
                    return 3.432666
                else:
                    return -0.470788
        else:
            if acs <= 126.000000:
                if kills_per_round <= 0.369565:
                    return -0.164525
                else:
                    return -5.501345
            else:
                if dda <= -2.500000:
                    return 3.157639
                else:
                    return 0.024621
    score += 0.100000 * tree_150()

    def tree_151():
        if deaths_per_round <= 0.893797:
            if kast_rate <= 0.615000:
                if acs <= 236.000000:
                    return -0.630544
                else:
                    return -7.223640
            else:
                if hs_rate <= 0.085000:
                    return 3.679825
                else:
                    return 0.023266
        else:
            if dda <= -49.500000:
                if fk_per_round <= 0.051316:
                    return -3.509174
                else:
                    return 0.252097
            else:
                if kast_rate <= 0.685000:
                    return 4.095682
                else:
                    return 1.641835
    score += 0.100000 * tree_151()

    def tree_152():
        if player_rank_idx <= 5.500000:
            if deaths_per_round <= 0.875000:
                if rank_delta <= -0.500000:
                    return -0.745197
                else:
                    return -2.821845
            else:
                return 4.993944
        else:
            if plus_minus <= -5.500000:
                if dda <= -40.500000:
                    return -0.137388
                else:
                    return 4.242573
            else:
                if kills_per_round <= 0.443627:
                    return -10.408190
                else:
                    return -0.063753
    score += 0.100000 * tree_152()

    def tree_153():
        if hs_rate <= 0.565000:
            if kast_rate <= 0.845000:
                if avg_rank_idx <= 21.500000:
                    return -0.354325
                else:
                    return 0.746150
            else:
                if dda <= 34.500000:
                    return 3.379951
                else:
                    return 0.441357
        else:
            return -2.832980
    score += 0.100000 * tree_153()

    def tree_154():
        if fd_per_round <= 0.177521:
            if hs_rate <= 0.645000:
                if round_diff <= -0.184265:
                    return -1.323843
                else:
                    return 0.321505
            else:
                return -8.414634
        else:
            if deaths_per_round <= 0.780193:
                if assists_per_round <= 0.096154:
                    return 4.555279
                else:
                    return -3.524006
            else:
                if mk_per_round <= 0.109127:
                    return -0.037234
                else:
                    return 4.625743
    score += 0.100000 * tree_154()

    def tree_155():
        if log_kill_death <= -0.279808:
            if kills_per_round <= 0.446558:
                if kast_rate <= 0.765000:
                    return -1.065139
                else:
                    return 4.436675
            else:
                if fd_per_round <= 0.085145:
                    return 4.251577
                else:
                    return -0.055202
        else:
            if acs <= 181.500000:
                if fd_per_round <= 0.110324:
                    return -0.584166
                else:
                    return -6.495689
            else:
                if log_kill_death <= -0.192606:
                    return -3.482333
                else:
                    return 0.426690
    score += 0.100000 * tree_155()

    def tree_156():
        if deaths_per_round <= 0.893797:
            if acs <= 221.500000:
                if acs <= 210.500000:
                    return -0.121820
                else:
                    return 4.083909
            else:
                if dda <= 11.000000:
                    return -4.535871
                else:
                    return 0.136006
        else:
            if dda <= -49.500000:
                if fk_per_round <= 0.051316:
                    return -3.035248
                else:
                    return 0.477763
            else:
                if kast_rate <= 0.685000:
                    return 3.600006
                else:
                    return 1.479473
    score += 0.100000 * tree_156()

    def tree_157():
        if log_kill_death <= -0.050042:
            if adr <= 140.050003:
                if adr <= 131.650002:
                    return 0.243200
                else:
                    return -2.753173
            else:
                if deaths_per_round <= 0.848077:
                    return 6.117599
                else:
                    return 0.625528
        else:
            if fk_per_round <= 0.040064:
                if adr <= 160.600006:
                    return 4.428980
                else:
                    return -0.008944
            else:
                if acs <= 263.500000:
                    return -1.522730
                else:
                    return 0.368165
    score += 0.100000 * tree_157()

    def tree_158():
        if player_rank_idx <= 5.500000:
            if deaths_per_round <= 0.875000:
                if round_diff <= 0.215217:
                    return -0.949887
                else:
                    return -3.438803
            else:
                return 4.255899
        else:
            if player_rank_idx <= 7.500000:
                if assists_per_round <= 0.326087:
                    return -0.204029
                else:
                    return 4.632168
            else:
                if acs <= 175.500000:
                    return -0.633112
                else:
                    return 0.209182
    score += 0.100000 * tree_158()

    def tree_159():
        if dda <= -4.500000:
            if dda <= -13.500000:
                if assists_per_round <= 0.091097:
                    return 2.241368
                else:
                    return -0.483543
            else:
                if rank_delta <= 0.500000:
                    return 6.819512
                else:
                    return 0.669999
        else:
            if dda <= 10.500000:
                if hs_rate <= 0.315000:
                    return -3.914900
                else:
                    return 2.192985
            else:
                if kast_rate <= 0.745000:
                    return 1.443744
                else:
                    return -0.647802
    score += 0.100000 * tree_159()

    def tree_160():
        if assists_per_round <= 0.045549:
            if fk_per_round <= 0.040064:
                return 6.313026
            else:
                if rank_delta <= 1.500000:
                    return -3.506900
                else:
                    return 1.362137
        else:
            if assists_per_round <= 0.085145:
                if rank_delta <= 0.500000:
                    return 6.825877
                else:
                    return 0.709316
            else:
                if fd_per_round <= 0.182195:
                    return 0.166114
                else:
                    return -1.234513
    score += 0.100000 * tree_160()

    def tree_161():
        if hs_rate <= 0.565000:
            if hs_rate <= 0.510000:
                if dda <= 33.500000:
                    return 0.190882
                else:
                    return -0.603300
            else:
                return 3.484570
        else:
            return -2.729748
    score += 0.100000 * tree_161()

    def tree_162():
        if round_diff <= 0.106884:
            if assists_per_round <= 0.419872:
                if assists_per_round <= 0.360681:
                    return -0.204108
                else:
                    return 2.197075
            else:
                if fd_per_round <= 0.046739:
                    return -4.045385
                else:
                    return -0.143618
        else:
            if assists_per_round <= 0.255435:
                if fd_per_round <= 0.183473:
                    return 0.174878
                else:
                    return -2.477285
            else:
                if fd_per_round <= 0.051316:
                    return 0.161095
                else:
                    return 3.414417
    score += 0.100000 * tree_162()

    def tree_163():
        if dda <= 81.000000:
            if dda <= 33.500000:
                if dda <= 26.500000:
                    return -0.137724
                else:
                    return 3.683516
            else:
                if kills_per_round <= 0.834096:
                    return 2.703001
                else:
                    return -1.253189
        else:
            if hs_rate <= 0.435000:
                if log_kill_death <= 0.460994:
                    return 3.250707
                else:
                    return 1.238990
            else:
                return -2.300301
    score += 0.100000 * tree_163()

    def tree_164():
        if acs <= 221.500000:
            if acs <= 220.500000:
                if acs <= 193.500000:
                    return -0.219319
                else:
                    return 1.517659
            else:
                return 9.555039
        else:
            if kast_rate <= 0.675000:
                if deaths_per_round <= 0.847826:
                    return -3.848482
                else:
                    return 0.888386
            else:
                if kast_rate <= 0.745000:
                    return 1.651830
                else:
                    return -0.803307
    score += 0.100000 * tree_164()

    def tree_165():
        if log_kill_death <= -0.294981:
            if acs <= 143.500000:
                if kast_rate <= 0.760000:
                    return -0.961621
                else:
                    return 4.897880
            else:
                if rank_delta <= -0.500000:
                    return -3.061159
                else:
                    return 3.257437
        else:
            if kast_rate <= 0.515000:
                return -5.219550
            else:
                if dda <= -26.500000:
                    return -1.535790
                else:
                    return 0.149332
    score += 0.100000 * tree_165()

    def tree_166():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.017857:
                if deaths_per_round <= 0.784722:
                    return -2.689519
                else:
                    return 0.399033
            else:
                if assists_per_round <= 0.419872:
                    return 0.228098
                else:
                    return -2.027337
        else:
            if adr <= 147.950005:
                if adr <= 126.250000:
                    return -0.035275
                else:
                    return 4.817958
            else:
                if kast_rate <= 0.660000:
                    return -4.885522
                else:
                    return 0.225411
    score += 0.100000 * tree_166()

    def tree_167():
        if kills_per_round <= 0.522774:
            if adr <= 117.750000:
                if kills_per_round <= 0.472136:
                    return -0.473323
                else:
                    return 2.174040
            else:
                return 7.877996
        else:
            if acs <= 159.500000:
                if round_diff <= 0.000000:
                    return -1.325234
                else:
                    return -5.426788
            else:
                if assists_per_round <= 0.422065:
                    return 0.148660
                else:
                    return -1.449156
    score += 0.100000 * tree_167()

    def tree_168():
        if kast_rate <= 0.845000:
            if acs <= 221.500000:
                if acs <= 220.500000:
                    return 0.128098
                else:
                    return 8.546926
            else:
                if kast_rate <= 0.745000:
                    return 0.177987
                else:
                    return -1.809867
        else:
            if hs_rate <= 0.590000:
                if player_rank_idx <= 12.500000:
                    return 2.722973
                else:
                    return 0.458919
            else:
                return -7.115037
    score += 0.100000 * tree_168()

    def tree_169():
        if plus_minus <= 10.500000:
            if plus_minus <= 9.500000:
                if plus_minus <= 8.500000:
                    return -0.059439
                else:
                    return 4.025577
            else:
                if kast_rate <= 0.755000:
                    return -6.285916
                else:
                    return -0.998506
        else:
            if mk_per_round <= 0.040064:
                return 3.642665
            else:
                if assists_per_round <= 0.127717:
                    return -0.206577
                else:
                    return 1.188453
    score += 0.100000 * tree_169()

    def tree_170():
        if round_diff <= 0.106884:
            if player_rank_idx <= 23.500000:
                if player_rank_idx <= 21.500000:
                    return -0.453004
                else:
                    return 0.884978
            else:
                if acs <= 182.500000:
                    return -9.757356
                else:
                    return -1.660790
        else:
            if hs_rate <= 0.135000:
                if assists_per_round <= 0.093478:
                    return 9.533754
                else:
                    return 1.767760
            else:
                if acs <= 150.000000:
                    return -1.943841
                else:
                    return 0.446481
    score += 0.100000 * tree_170()

    def tree_171():
        if log_kill_death <= -0.279808:
            if dda <= -40.500000:
                if deaths_per_round <= 0.639423:
                    return -8.686752
                else:
                    return 0.075750
            else:
                if dda <= -22.500000:
                    return 3.422857
                else:
                    return -0.442228
        else:
            if dda <= -26.500000:
                if adr <= 107.000000:
                    return -4.958183
                else:
                    return -0.819447
            else:
                if plus_minus <= -4.500000:
                    return -8.111122
                else:
                    return 0.158258
    score += 0.100000 * tree_171()

    def tree_172():
        if log_kill_death <= -0.050042:
            if fd_per_round <= 0.048810:
                if player_rank_idx <= 10.500000:
                    return -1.967943
                else:
                    return 2.824981
            else:
                if mk_per_round <= 0.080128:
                    return -0.569774
                else:
                    return 3.007058
        else:
            if dda <= 10.500000:
                if adr <= 159.450005:
                    return -0.586214
                else:
                    return -6.333633
            else:
                if kast_rate <= 0.745000:
                    return 1.092772
                else:
                    return -0.540135
    score += 0.100000 * tree_172()

    def tree_173():
        if log_kill_death <= -0.294981:
            if acs <= 143.500000:
                if kast_rate <= 0.760000:
                    return -0.696142
                else:
                    return 4.032995
            else:
                if rank_delta <= -0.500000:
                    return -2.890667
                else:
                    return 2.809725
        else:
            if kast_rate <= 0.515000:
                return -4.644868
            else:
                if acs <= 181.500000:
                    return -1.010965
                else:
                    return 0.161199
    score += 0.100000 * tree_173()

    def tree_174():
        if round_diff <= -0.106884:
            if assists_per_round <= 0.620205:
                if deaths_per_round <= 0.704969:
                    return -1.986055
                else:
                    return 0.061094
            else:
                return -9.179145
        else:
            if kast_rate <= 0.605000:
                if assists_per_round <= 0.085145:
                    return 1.160282
                else:
                    return -2.349390
            else:
                if kast_rate <= 0.675000:
                    return 1.752951
                else:
                    return 0.060681
    score += 0.100000 * tree_174()

    def tree_175():
        if acs <= 221.500000:
            if acs <= 220.500000:
                if kast_rate <= 0.680000:
                    return 0.744109
                else:
                    return -0.491468
            else:
                return 7.593505
        else:
            if dda <= 11.000000:
                if hs_rate <= 0.245000:
                    return -4.303232
                else:
                    return 0.744729
            else:
                if adr <= 141.800003:
                    return 12.752401
                else:
                    return -0.008670
    score += 0.100000 * tree_175()

    def tree_176():
        if assists_per_round <= 0.045549:
            if avg_rank_idx <= 21.000000:
                if mk_per_round <= 0.046739:
                    return -4.376558
                else:
                    return 0.923220
            else:
                if kast_rate <= 0.770000:
                    return -2.421554
                else:
                    return -9.150931
        else:
            if assists_per_round <= 0.085145:
                if rank_delta <= 0.500000:
                    return 5.738282
                else:
                    return 0.620275
            else:
                if fd_per_round <= 0.155870:
                    return 0.170736
                else:
                    return -0.807809
    score += 0.100000 * tree_176()

    def tree_177():
        if hs_rate <= 0.105000:
            if kills_per_round <= 0.923077:
                if fd_per_round <= 0.040064:
                    return -3.558708
                else:
                    return 0.985730
            else:
                return 9.716383
        else:
            if hs_rate <= 0.145000:
                if round_diff <= -0.074176:
                    return -3.344081
                else:
                    return 1.507810
            else:
                if kills_per_round <= 0.837719:
                    return 0.336217
                else:
                    return -0.441616
    score += 0.100000 * tree_177()

    def tree_178():
        if dda <= 58.500000:
            if dda <= 47.500000:
                if acs <= 266.000000:
                    return -0.111549
                else:
                    return 1.550838
            else:
                if rank_delta <= 14.000000:
                    return -4.872906
                else:
                    return 1.751076
        else:
            if assists_per_round <= 0.302174:
                if mk_per_round <= 0.040064:
                    return 3.780736
                else:
                    return 0.154780
            else:
                if avg_rank_idx <= 14.500000:
                    return 3.960257
                else:
                    return 1.917929
    score += 0.100000 * tree_178()

    def tree_179():
        if deaths_per_round <= 0.883484:
            if deaths_per_round <= 0.763305:
                if fd_per_round <= 0.183473:
                    return 0.388857
                else:
                    return -1.859007
            else:
                if mk_per_round <= 0.127717:
                    return -0.888526
                else:
                    return 1.952723
        else:
            if adr <= 161.400002:
                if fd_per_round <= 0.093478:
                    return 1.523338
                else:
                    return -0.439263
            else:
                if fk_per_round <= 0.187643:
                    return 3.781010
                else:
                    return 0.178161
    score += 0.100000 * tree_179()

    def tree_180():
        if kills_per_round <= 0.522774:
            if adr <= 117.750000:
                if deaths_per_round <= 0.638587:
                    return -3.356705
                else:
                    return 0.534320
            else:
                return 6.777474
        else:
            if acs <= 159.500000:
                if kast_rate <= 0.695000:
                    return -1.140711
                else:
                    return -4.692518
            else:
                if assists_per_round <= 0.422065:
                    return 0.125885
                else:
                    return -1.272869
    score += 0.100000 * tree_180()

    def tree_181():
        if acs <= 221.500000:
            if adr <= 140.050003:
                if avg_rank_idx <= 20.500000:
                    return -0.322919
                else:
                    return 1.082979
            else:
                if acs <= 213.000000:
                    return 1.956823
                else:
                    return 8.696705
        else:
            if kast_rate <= 0.675000:
                if hs_rate <= 0.285000:
                    return -4.400634
                else:
                    return -0.594734
            else:
                if kast_rate <= 0.745000:
                    return 1.312486
                else:
                    return -0.621959
    score += 0.100000 * tree_181()

    def tree_182():
        if hs_rate <= 0.105000:
            if kills_per_round <= 0.923077:
                if fd_per_round <= 0.040064:
                    return -2.964693
                else:
                    return 0.928204
            else:
                return 8.406938
        else:
            if hs_rate <= 0.145000:
                if round_diff <= -0.074176:
                    return -2.904714
                else:
                    return 1.400654
            else:
                if kills_per_round <= 0.837719:
                    return 0.297987
                else:
                    return -0.428337
    score += 0.100000 * tree_182()

    def tree_183():
        if kast_rate <= 0.845000:
            if acs <= 221.500000:
                if acs <= 211.500000:
                    return 0.001930
                else:
                    return 2.862384
            else:
                if adr <= 161.349998:
                    return -1.856948
                else:
                    return 0.077348
        else:
            if hs_rate <= 0.590000:
                if dda <= 34.500000:
                    return 2.584976
                else:
                    return 0.463950
            else:
                return -6.115886
    score += 0.100000 * tree_183()

    def tree_184():
        if deaths_per_round <= 0.883484:
            if deaths_per_round <= 0.763305:
                if fd_per_round <= 0.183473:
                    return 0.355542
                else:
                    return -1.718527
            else:
                if mk_per_round <= 0.127717:
                    return -0.826178
                else:
                    return 1.785062
        else:
            if kills_per_round <= 0.744565:
                if kast_rate <= 0.515000:
                    return 1.836170
                else:
                    return -0.564374
            else:
                if assists_per_round <= 0.224080:
                    return 3.915627
                else:
                    return 1.381778
    score += 0.100000 * tree_184()

    def tree_185():
        if kd <= 0.750000:
            if acs <= 143.500000:
                if log_kill_death <= -0.315402:
                    return -0.545855
                else:
                    return 5.239263
            else:
                if rank_delta <= -0.500000:
                    return -2.389252
                else:
                    return 2.206235
        else:
            if dda <= -26.500000:
                if adr <= 107.000000:
                    return -4.256120
                else:
                    return -0.702124
            else:
                if plus_minus <= -4.500000:
                    return -6.965498
                else:
                    return 0.128022
    score += 0.100000 * tree_185()

    def tree_186():
        if log_kill_death <= -0.055613:
            if log_kill_death <= -0.058892:
                if rank_delta <= 1.500000:
                    return 0.637119
                else:
                    return -0.508486
            else:
                if player_rank_idx <= 7.500000:
                    return -3.929950
                else:
                    return 6.179779
        else:
            if dda <= 10.500000:
                if dda <= -1.500000:
                    return 0.300995
                else:
                    return -3.809620
            else:
                if deaths_per_round <= 0.733806:
                    return 0.694554
                else:
                    return -0.709450
    score += 0.100000 * tree_186()

    def tree_187():
        if round_diff <= -0.106884:
            if dda <= -4.500000:
                if dda <= -7.500000:
                    return 0.063528
                else:
                    return 10.163907
            else:
                if assists_per_round <= 0.097619:
                    return -4.161497
                else:
                    return -0.590458
        else:
            if round_diff <= -0.080128:
                if adr <= 96.049999:
                    return -3.286771
                else:
                    return 3.968880
            else:
                if kast_rate <= 0.605000:
                    return -1.782645
                else:
                    return 0.198115
    score += 0.100000 * tree_187()

    def tree_188():
        if kills_per_round <= 0.522774:
            if adr <= 117.750000:
                if deaths_per_round <= 0.638587:
                    return -2.932058
                else:
                    return 0.510933
            else:
                return 5.909375
        else:
            if acs <= 159.500000:
                if rank_delta <= 3.000000:
                    return -3.863642
                else:
                    return -0.666372
            else:
                if assists_per_round <= 0.425824:
                    return 0.084302
                else:
                    return -1.231260
    score += 0.100000 * tree_188()

    def tree_189():
        if acs <= 345.000000:
            if dda <= 33.500000:
                if dda <= 26.500000:
                    return -0.094763
                else:
                    return 2.885340
            else:
                if deaths_per_round <= 0.701993:
                    return 0.046261
                else:
                    return -2.124621
        else:
            if adr <= 266.099991:
                if kd <= 1.650000:
                    return 2.668885
                else:
                    return 1.283766
            else:
                return 0.001240
    score += 0.100000 * tree_189()

    def tree_190():
        if log_kill_death <= -0.055613:
            if log_kill_death <= -0.058892:
                if fd_per_round <= 0.093478:
                    return 0.659050
                else:
                    return -0.408673
            else:
                if player_rank_idx <= 7.500000:
                    return -3.542262
                else:
                    return 5.471845
        else:
            if rank_delta <= 1.500000:
                if log_kill_death <= 0.204155:
                    return -1.992422
                else:
                    return 0.551330
            else:
                if mk_per_round <= 0.042572:
                    return 3.649510
                else:
                    return -0.355043
    score += 0.100000 * tree_190()

    def tree_191():
        if round_diff <= 0.106884:
            if fk_per_round <= 0.017857:
                if plus_minus <= -3.500000:
                    return -0.243849
                else:
                    return -3.093248
            else:
                if fk_per_round <= 0.074176:
                    return 0.801978
                else:
                    return -0.311054
        else:
            if adr <= 147.950005:
                if adr <= 126.250000:
                    return 0.079093
                else:
                    return 3.858785
            else:
                if kast_rate <= 0.660000:
                    return -3.902104
                else:
                    return 0.116024
    score += 0.100000 * tree_191()

    def tree_192():
        if fk_per_round <= 0.233032:
            if log_kill_death <= -0.055613:
                if log_kill_death <= -0.058892:
                    return 0.107486
                else:
                    return 3.310966
            else:
                if rank_delta <= 1.500000:
                    return -1.047718
                else:
                    return 0.458467
        else:
            if deaths_per_round <= 0.651087:
                return -2.311283
            else:
                if kills_per_round <= 0.891304:
                    return 3.654362
                else:
                    return 0.348265
    score += 0.100000 * tree_192()

    def tree_193():
        if hs_rate <= 0.105000:
            if kills_per_round <= 0.923077:
                if avg_rank_idx <= 10.500000:
                    return 0.784081
                else:
                    return -2.460863
            else:
                return 7.204666
        else:
            if hs_rate <= 0.145000:
                if round_diff <= -0.074176:
                    return -2.469675
                else:
                    return 1.223165
            else:
                if kills_per_round <= 0.837719:
                    return 0.254706
                else:
                    return -0.370860
    score += 0.100000 * tree_193()

    def tree_194():
        if kast_rate <= 0.845000:
            if assists_per_round <= 0.659420:
                if assists_per_round <= 0.651087:
                    return -0.074656
                else:
                    return -7.533003
            else:
                return 5.397228
        else:
            if hs_rate <= 0.590000:
                if dda <= 34.500000:
                    return 2.221560
                else:
                    return 0.409547
            else:
                return -5.010097
    score += 0.100000 * tree_194()

    def tree_195():
        if acs <= 339.500000:
            if mk_per_round <= 0.219807:
                if mk_per_round <= 0.208696:
                    return -0.056396
                else:
                    return 3.766012
            else:
                return -5.313009
        else:
            if player_rank_idx <= 23.000000:
                if adr <= 266.099991:
                    return 1.537101
                else:
                    return 0.027605
            else:
                return -1.205254
    score += 0.100000 * tree_195()

    def tree_196():
        if deaths_per_round <= 0.883484:
            if round_diff <= -0.106884:
                if adr <= 123.700001:
                    return 0.320031
                else:
                    return -1.212822
            else:
                if round_diff <= -0.080128:
                    return 1.826871
                else:
                    return -0.069224
        else:
            if hs_rate <= 0.470000:
                if assists_per_round <= 0.280435:
                    return 1.114336
                else:
                    return -0.448860
            else:
                return 3.988913
    score += 0.100000 * tree_196()

    def tree_197():
        if kast_rate <= 0.845000:
            if assists_per_round <= 0.659420:
                if assists_per_round <= 0.651087:
                    return -0.068645
                else:
                    return -6.652781
            else:
                return 4.870067
        else:
            if hs_rate <= 0.590000:
                if player_rank_idx <= 12.500000:
                    return 1.962762
                else:
                    return 0.322739
            else:
                return -4.496525
    score += 0.100000 * tree_197()

    def tree_198():
        if fk_per_round <= 0.233032:
            if log_kill_death <= -0.294981:
                if acs <= 143.500000:
                    return -0.382999
                else:
                    return 1.318858
            else:
                if kast_rate <= 0.515000:
                    return -3.796409
                else:
                    return -0.139142
        else:
            if deaths_per_round <= 0.651087:
                return -2.122427
            else:
                if kills_per_round <= 0.891304:
                    return 3.189538
                else:
                    return 0.282843
    score += 0.100000 * tree_198()

    def tree_199():
        if acs <= 263.500000:
            if kills_per_round <= 0.902950:
                if dda <= 26.500000:
                    return -0.120478
                else:
                    return 1.503719
            else:
                if adr <= 155.800003:
                    return -9.705828
                else:
                    return -2.173499
        else:
            if dda <= 34.000000:
                if dda <= 11.000000:
                    return -1.393646
                else:
                    return 4.998357
            else:
                if plus_minus <= 4.500000:
                    return -2.459117
                else:
                    return 0.284446
    score += 0.100000 * tree_199()

    return score

# AWB Offset Map 配置详解（offset_map01–116）

本文基于 `tests/test_data/awb_scenario_1x.xml` 中的 `offset_map01` 至 `offset_map116` 配置，结合 `AGENTS.md` 对 AWB 几何映射、参考白点与增益关系的说明，对每一张 offset map 的几何覆盖、目标坐标、映射方式与触发条件进行逐项梳理，并总结室内、室外与夜景三大场景族群的整体规律。

## 单张 offset map 逐项分析

### offset_map01 — 1_BlueSky_HgihEV
- 场景标签：BlueSky_HgihEV（主类 BlueSky，归类为室外场景）
- 几何覆盖：4 个顶点；RpG 范围 0.3003–0.4475；BpG 范围 0.7946–1.0167
- 目标坐标：(0.5104, 0.6147)，最近参考白点 D50（距离 0.00473）；强拉至单点；权重 0.2
- **额外观察**：从多边形质心拉动距离≈0.3217
- 触发条件：e_ratio[0,1]；BV[9.9,15]；CT[5000,12000]；IR[0.27,999]；Count[450,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map02 — 2_BlueSky_LowLight
- 场景标签：BlueSky_LowLight（主类 BlueSky，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.2609–0.4331；BpG 范围 0.8811–1.1526
- 目标坐标：(0.5104, 0.6147)，最近参考白点 D50（距离 0.00473）；强拉至单点；权重 0.15
- **额外观察**：从多边形质心拉动距离≈0.4322
- 触发条件：e_ratio[0,1]；BV[7.3,10]；CT[5000,12000]；IR[0.2,999]；Count[450,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map03 — 3_BrightOutdoor_D50HighBV
- 场景标签：BrightOutdoor_D50HighBV（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3504–0.4812；BpG 范围 0.622–0.7114
- 目标坐标：(0.5206, 0.6209)，最近参考白点 D50（距离 0.01625）；强拉至单点；权重 0.5
- **额外观察**：从多边形质心拉动距离≈0.1182
- 触发条件：e_ratio[0,1]；BV[10,15]；CT[5500,12000]；IR[0.34,999]；Count[400,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map04 — 4_BlueSky_SnowLowLight
- 场景标签：BlueSky_SnowLowLight（主类 BlueSky，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3306–0.447；BpG 范围 0.8504–0.9973
- 目标坐标：(0.01, -0.035)，最近参考白点 F（距离 0.77471）；整体位移；权重 1
- **额外观察**：从多边形质心拉动距离≈1.0321
- 触发条件：e_ratio[0,0]；BV[0,4.2]；CT[8000,12000]；IR[0.25,999]；Count[1,3072]；ColorCT[4900,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map05 — 5_BlueSky_GreySkyLowLight
- 场景标签：BlueSky_GreySkyLowLight（主类 BlueSky，归类为室外场景）
- 几何覆盖：5 个顶点；RpG 范围 0.3028–0.4344；BpG 范围 0.7427–0.958
- 目标坐标：(0.035, -0.1)，最近参考白点 F（距离 0.80233）；整体位移；权重 0.6
- **额外观察**：从多边形质心拉动距离≈0.9979
- 触发条件：e_ratio[0,1]；BV[1,7]；CT[6800,12000]；IR[0.15,999]；Count[800,3072]；ColorCT[5200,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map06 — 6_BlueSky_snowWithBlueSky
- 场景标签：BlueSky_snowWithBlueSky（主类 BlueSky，归类为室外场景）
- 几何覆盖：5 个顶点；RpG 范围 0.3744–0.5578；BpG 范围 0.7036–0.8499
- 目标坐标：(0.02, 0.02)，最近参考白点 F（距离 0.73123）；整体位移；权重 1
- 触发条件：e_ratio[0,0]；BV[8,15]；CT[6100,12000]；IR[0.5,999]；Count[1,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map07 — 7_BlueSky_GreySkyHigh
- 场景标签：BlueSky_GreySkyHigh（主类 BlueSky，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3024–0.4344；BpG 范围 0.7503–0.958
- 目标坐标：(0.0924, -0.1009)，最近参考白点 F（距离 0.76485）；整体位移；权重 0.4
- 触发条件：e_ratio[0,1]；BV[6.7,15]；CT[5100,12000]；IR[0.15,999]；Count[1,3072]；ColorCT[5300,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map08 — 8_BlueSky_BlueStats
- 场景标签：BlueSky_BlueStats（主类 BlueSky，归类为室外场景）
- 几何覆盖：4 个顶点；RpG 范围 0.2127–0.3237；BpG 范围 0.7246–0.9242
- 目标坐标：(0.5111, 0.6457)，最近参考白点 D50（距离 0.03519）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[4,15]；CT[5000,12000]；IR[0.15,999]；Count[800,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map09 — 9_BlueSky_BlueStats_HighBV
- 场景标签：BlueSky_BlueStats_HighBV（主类 BlueSky，归类为室外场景）
- 几何覆盖：4 个顶点；RpG 范围 0.4146–0.5005；BpG 范围 0.8438–0.973
- 目标坐标：(0.5111, 0.6457)，最近参考白点 D50（距离 0.03519）；强拉至单点；权重 0.12
- 触发条件：e_ratio[0,1]；BV[7.5,15]；CT[5000,12000]；IR[0.3,999]；Count[1000,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map10 — 10_outdoor_BlueMoment_2
- 场景标签：outdoor_BlueMoment_2（主类 outdoor，归类为室外场景）；当前在 amapParam 中标记为未启用
- 几何覆盖：0 个顶点；RpG 范围 0.253–0.3854；BpG 范围 0.6466–0.7475
- 目标坐标：(0.01, -0.02)，最近参考白点 F（距离 0.76474）；整体位移；权重 0.5
- 触发条件：e_ratio[0,0]；BV[8.3,15]；CT[6800,12000]；IR[0.4,999]；Count[1200,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map11 — 11_BrightOutdoor_SkyGrass
- 场景标签：BrightOutdoor_SkyGrass（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3505–0.5178；BpG 范围 0.6337–0.7618
- 目标坐标：(0.0371, -0.0158)，最近参考白点 F（距离 0.74171）；整体位移；权重 0.5
- 触发条件：e_ratio[0,0]；BV[7.7,8.7]；CT[5400,12000]；IR[0.45,1]；Count[1,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map12 — 12_Indoor_LowMixHigh
- 场景标签：Indoor_LowMixHigh（主类 Indoor，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.3343–0.4812；BpG 范围 0.7397–0.8639
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 2.2
- 触发条件：e_ratio[0,0]；BV[-0.5,4.9]；CT[4000,7400]；IR[0.3,999]；Count[500,1700]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,900]

### offset_map13 — 13_BrightOutdoor_IndoorHighMixMidstats
- 场景标签：BrightOutdoor_IndoorHighMixMidstats（主类 BrightOutdoor，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.5632–0.7175；BpG 范围 0.5133–0.598
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[2,4.5]；CT[5100,12000]；IR[0,0.1]；Count[1,600]；ColorCT[5300,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map14 — 14_BrightOutdoor_LLhtHighMixMid
- 场景标签：BrightOutdoor_LLhtHighMixMid（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4308–0.7669；BpG 范围 0.3823–0.6337
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-1,2]；CT[5000,12000]；IR[0.31,999]；Count[1,750]；ColorCT[5300,12000]；DiffCT[1,9000]；Y[1,255]；FaceCT[0,9000]

### offset_map15 — 15_BrightOutdoor_GreySky_face
- 场景标签：BrightOutdoor_GreySky_face（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：8 个顶点；RpG 范围 0.3502–0.5021；BpG 范围 0.7166–0.8021
- 目标坐标：(0.0324, -0.0652)，最近参考白点 F（距离 0.7792）；整体位移；权重 0.5
- 触发条件：e_ratio[0,1]；BV[8,15]；CT[5200,8500]；IR[0.5,999]；Count[900,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[4000,9000]

### offset_map16 — 16_BrightOutdoor_GreenLake
- 场景标签：BrightOutdoor_GreenLake（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.2933–0.4888；BpG 范围 0.59–0.7844
- 目标坐标：(0.5104, 0.6147)，最近参考白点 D50（距离 0.00473）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[7.8,15]；CT[4800,12000]；IR[0.3,999]；Count[150,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map17 — 17_BrightOutdoor_GreySky_scene
- 场景标签：BrightOutdoor_GreySky_scene（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.3642–0.5021；BpG 范围 0.721–0.811
- 目标坐标：(0.0321, -0.0602)，最近参考白点 F（距离 0.7759）；整体位移；权重 0.5
- 触发条件：e_ratio[1,1]；BV[1,15]；CT[5200,8500]；IR[0.45,999]；Count[900,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,900]

### offset_map18 — 18_GreenZone_MidStats_Face_Highlight
- 场景标签：GreenZone_MidStats_Face_Highlight（主类 GreenZone，归类为室外场景）
- 几何覆盖：13 个顶点；RpG 范围 0.4263–1.2869；BpG 范围 0.1575–0.6168
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[6.41,15]；CT[3300,5200]；IR[0.48,999]；Count[1,3072]；ColorCT[5000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[5400,9000]

### offset_map19 — 19_BrightOutdoor_Wood_y
- 场景标签：BrightOutdoor_Wood_y（主类 BrightOutdoor，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.5214–1.0959；BpG 范围 0.2583–0.5516
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；强拉至单点；权重 0.1
- 触发条件：e_ratio[0,1]；BV[2.5,18]；CT[4600,12000]；IR[0.5,999]；Count[450,2000]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map20 — 20_GreenZone_Shade_y
- 场景标签：GreenZone_Shade_y（主类 GreenZone，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.2058–0.5921；BpG 范围 0.1715–0.459
- 目标坐标：(0.4657, 0.6363)，最近参考白点 D50（距离 0.04938）；强拉至单点；权重 0.6
- 触发条件：e_ratio[0,1]；BV[2.5,15]；CT[2000,12000]；IR[0.5,999]；Count[450,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map21 — 21_GreenZone_YellowStatsHighIR
- 场景标签：GreenZone_YellowStatsHighIR（主类 GreenZone，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.6708–0.81；BpG 范围 0.4544–0.5587
- 目标坐标：(0.5155, 0.6147)，最近参考白点 D50（距离 0.00854）；强拉至单点；权重 0.3
- 触发条件：e_ratio[0,0]；BV[0,5]；CT[3100,5200]；IR[1.1,999]；Count[1,3072]；ColorCT[5000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map22 — 22_GreenZone_InGreyZone_y
- 场景标签：GreenZone_InGreyZone_y（主类 GreenZone，归类为室外场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4283–0.6533；BpG 范围 0.3593–0.5611
- 目标坐标：(0.5105, 0.6234)，最近参考白点 D50（距离 0.01296）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[2,15]；CT[3500,12000]；IR[0.5,999]；Count[1,2000]；ColorCT[3700,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map23 — 23_GreenZone_25_MidStats_scene
- 场景标签：GreenZone_25_MidStats_scene（主类 GreenZone，归类为室外场景）
- 几何覆盖：13 个顶点；RpG 范围 0.4263–1.2869；BpG 范围 0.1575–0.5924
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[2,5.2]；CT[2800,12000]；IR[0.5,999]；Count[1,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,800]

### offset_map24 — 24_GreenZone_HightLowLightD65_y
- 场景标签：GreenZone_HightLowLightD65_y（主类 GreenZone，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.116–0.4618；BpG 范围 0.3805–0.6614
- 目标坐标：(0.4581, 0.7303)，最近参考白点 D65（距离 0.01161）；强拉至单点；权重 0.8
- 触发条件：e_ratio[0,1]；BV[2.5,15]；CT[3600,12000]；IR[0.5,999]；Count[400,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map25 — 25_GreenZone_MidStats_scene
- 场景标签：GreenZone_MidStats_scene（主类 GreenZone，归类为室外场景）
- 几何覆盖：13 个顶点；RpG 范围 0.4262–1.2898；BpG 范围 0.1575–0.5836
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[5.3,15]；CT[2800,12000]；IR[0.35,999]；Count[400,3072]；ColorCT[4800,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,800]

### offset_map26 — 26_GreenZone_indoor_green_y
- 场景标签：GreenZone_indoor_green_y（主类 GreenZone，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.1618–0.4036；BpG 范围 0.4838–0.6546
- 目标坐标：(0.463, 0.7288)，最近参考白点 D65（距离 0.01479）；强拉至单点；权重 0.6
- 触发条件：e_ratio[0,1]；BV[-1,4]；CT[3600,12000]；IR[0.5,0.3]；Count[400,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map27 — 27_GreenZone_HightEV_InGreyzone_y
- 场景标签：GreenZone_HightEV_InGreyzone_y（主类 GreenZone，归类为室外场景）
- 几何覆盖：14 个顶点；RpG 范围 0.405–0.7384；BpG 范围 0.3073–0.6082
- 目标坐标：(0.5104, 0.6089)，最近参考白点 D50（距离 0.00306）；强拉至单点；权重 0.22
- 触发条件：e_ratio[0,1]；BV[6.3,18]；CT[3600,12000]；IR[0.35,999]；Count[400,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map28 — 28_GreenZone_GreenStatsLow_y
- 场景标签：GreenZone_GreenStatsLow_y（主类 GreenZone，归类为室外场景）
- 几何覆盖：8 个顶点；RpG 范围 0.3894–0.581；BpG 范围 0.3842–0.6376
- 目标坐标：(0.04, 0.035)，最近参考白点 F（距离 0.70626）；整体位移；权重 0.05
- 触发条件：e_ratio[0,1]；BV[-1,2.4]；CT[4300,12000]；IR[0.88,999]；Count[100,1200]；ColorCT[5100,12000]；DiffCT[1,9000]；Y[1,19]；FaceCT[0,9000]

### offset_map29 — 29_GreenZone_HighIRGreenInGreyZone
- 场景标签：GreenZone_HighIRGreenInGreyZone（主类 GreenZone，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.4742–0.6684；BpG 范围 0.4436–0.5856
- 目标坐标：(0.5154, 0.609)，最近参考白点 D50（距离 0.00772）；强拉至单点；权重 0.25
- 触发条件：e_ratio[0,0]；BV[3,5.3]；CT[3900,5000]；IR[0.95,999]；Count[300,3072]；ColorCT[5100,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map30 — 30_OutdoorScene_ExtremHighMixMid
- 场景标签：OutdoorScene_ExtremHighMixMid（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.478–0.813；BpG 范围 0.3705–0.6716
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[1,3.5]；CT[4900,12000]；IR[0.46,999]；Count[1,700]；ColorCT[5400,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map31 — 31_OutdoorScene_GreenWithMidStats
- 场景标签：OutdoorScene_GreenWithMidStats（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：5 个顶点；RpG 范围 0.4228–0.635；BpG 范围 0.5877–0.7036
- 目标坐标：(-0.05, 0.04)，最近参考白点 F（距离 0.77496）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[3.8,6.5]；CT[4400,4900]；IR[0.75,999]；Count[1,1600]；ColorCT[5200,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[7000,9000]

### offset_map32 — 32_GreenZone_MidStats_Face_Lowlight
- 场景标签：GreenZone_MidStats_Face_Lowlight（主类 GreenZone，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.558–1.3561；BpG 范围 0.1862–0.5176
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0.5,6.5]；CT[3300,12000]；IR[0.48,999]；Count[1,2400]；ColorCT[3800,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[4800,9000]

### offset_map33 — 33_OutdoorScene_GreenStats
- 场景标签：OutdoorScene_GreenStats（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：8 个顶点；RpG 范围 0.3759–0.6331；BpG 范围 0.352–0.6692
- 目标坐标：(0.51, 0.61)，最近参考白点 D50（距离 0.00219）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[2,15]；CT[4500,12000]；IR[0.4,998]；Count[1,1600]；ColorCT[4500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map34 — 34_OutdoorScene_MixMidStats_scene
- 场景标签：OutdoorScene_MixMidStats_scene（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：11 个顶点；RpG 范围 0.6884–1.1663；BpG 范围 0.3953–0.5966
- 目标坐标：(0.455, 0.585)，最近参考白点 D50（距离 0.05881）；强拉至单点；权重 0.25
- 触发条件：e_ratio[0,1]；BV[5.7,15]；CT[3000,5500]；IR[0.52,999]；Count[1,2900]；ColorCT[4750,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,900]

### offset_map35 — 35_OutdoorScene_BlueBuildingMixIndoor
- 场景标签：OutdoorScene_BlueBuildingMixIndoor（主类 OutdoorScene，归类为室内场景）
- 几何覆盖：4 个顶点；RpG 范围 0.2796–0.3986；BpG 范围 0.6855–0.761
- 目标坐标：(0.02, -0.055)，最近参考白点 F（距离 0.78098）；整体位移；权重 0.3
- 触发条件：e_ratio[0,1]；BV[2,4]；CT[5300,6800]；IR[0.12,0.25]；Count[0,1800]；ColorCT[5200,12000]；DiffCT[1,9000]；Y[55,254]；FaceCT[5100,5700]

### offset_map36 — 36_OutdoorScene_OutdoorPinkStats
- 场景标签：OutdoorScene_OutdoorPinkStats（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.5267–0.6112；BpG 范围 0.6063–0.7387
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.2
- 触发条件：e_ratio[0,1]；BV[4.7,10]；CT[4800,12000]；IR[0.5,999]；Count[2,3072]；ColorCT[5100,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map37 — 37_OutdoorScene_MixMidStats_Face
- 场景标签：OutdoorScene_MixMidStats_Face（主类 OutdoorScene，归类为室外场景）
- 几何覆盖：12 个顶点；RpG 范围 0.5867–1.1109；BpG 范围 0.3512–0.6063
- 目标坐标：(0.456, 0.585)，最近参考白点 D50（距离 0.05791）；强拉至单点；权重 0.25
- 触发条件：e_ratio[0,1]；BV[5.7,15]；CT[3000,4900]；IR[0.52,999]；Count[1,2900]；ColorCT[4750,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[2300,9000]

### offset_map38 — 38_sunset_HighEV
- 场景标签：sunset_HighEV（主类 sunset，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.6422–0.853；BpG 范围 0.348–0.5297
- 目标坐标：(0.44, 0.57)，最近参考白点 D50（距离 0.07916）；强拉至单点；权重 0.18
- 触发条件：e_ratio[0,1]；BV[7,15]；CT[2500,12000]；IR[0.75,999]；Count[1400,3072]；ColorCT[4000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map39 — 39_sunset_RedStats
- 场景标签：sunset_RedStats（主类 sunset，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 1.1303–2.48；BpG 范围 0.3527–0.6241
- 目标坐标：(0.44, 0.58)，最近参考白点 D50（距离 0.07452）；强拉至单点；权重 1
- 触发条件：e_ratio[0,1]；BV[6,15]；CT[2000,12000]；IR[0.5,999]；Count[1,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map40 — 40_outdoor_OrangeStatsInGrey
- 场景标签：outdoor_OrangeStatsInGrey（主类 outdoor，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.6416–0.77；BpG 范围 0.4581–0.5691
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.04
- 触发条件：e_ratio[0,1]；BV[4,5.5]；CT[3200,4400]；IR[0.4,999]；Count[140,3072]；ColorCT[4900,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[4600,9000]

### offset_map41 — 41_outdoor_Sunset
- 场景标签：outdoor_Sunset（主类 outdoor，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.5267–0.722；BpG 范围 0.7182–0.8346
- 目标坐标：(0.43, 0.595)，最近参考白点 D50（距离 0.07947）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[2,5]；CT[2400,12000]；IR[0.6,999]；Count[900,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1,9000]

### offset_map42 — 42_outdoor_BlueMoment
- 场景标签：outdoor_BlueMoment（主类 outdoor，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.2979–0.4445；BpG 范围 1.0097–1.1577
- 目标坐标：(0.36, 0.69)，最近参考白点 D65（距离 0.10864）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[-1,4]；CT[2000,12000]；IR[0.2,999]；Count[1200,3072]；ColorCT[4400,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1,1000]

### offset_map43 — 43_outdoor_BlueMoment_1
- 场景标签：outdoor_BlueMoment_1（主类 outdoor，归类为室外场景）
- 几何覆盖：5 个顶点；RpG 范围 0.2931–0.447；BpG 范围 1.1173–1.2607
- 目标坐标：(0.04, -0.3)，最近参考白点 F（距离 0.9549）；整体位移；权重 0.6
- 触发条件：e_ratio[0,1]；BV[-1,2]；CT[2000,12000]；IR[0.2,999]；Count[1200,3072]；ColorCT[4400,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1,1000]

### offset_map44 — 44_MixLight_indoor_bar
- 场景标签：MixLight_indoor_bar（主类 MixLight，归类为室内场景）
- 几何覆盖：12 个顶点；RpG 范围 0.3367–0.9577；BpG 范围 0.759–1.5308
- 目标坐标：(0.39, 0.65)，最近参考白点 D65（距离 0.11267）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[1,5]；CT[4500,12000]；IR[0,0.8]；Count[300,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map45 — 45_spatial_Outdoor_Pink_Face
- 场景标签：spatial_Outdoor_Pink_Face（主类 spatial，归类为室外场景）
- 几何覆盖：4 个顶点；RpG 范围 0.6213–1.5447；BpG 范围 0.4106–0.7951
- 目标坐标：(0.43, 0.59)，最近参考白点 D50（距离 0.08061）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[1,13]；CT[1700,5400]；IR[0.3,999]；Count[600,3072]；ColorCT[4000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[4000,6000]

### offset_map46 — 46_Indoor_LowMixHigh
- 场景标签：Indoor_LowMixHigh（主类 Indoor，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.3059–0.6093；BpG 范围 0.6016–0.9547
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-9,1]；CT[1500,7000]；IR[0,0.3]；Count[300,2400]；ColorCT[2000,5400]；DiffCT[1,9000]；Y[1,254]；FaceCT[2000,5800]

### offset_map47 — 47_Outdoor_IndoorHighMixMidstats
- 场景标签：Outdoor_IndoorHighMixMidstats（主类 Outdoor，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.5591–0.7417；BpG 范围 0.4452–0.5849
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[2,4.5]；CT[4500,12000]；IR[0.5,3]；Count[300,2400]；ColorCT[5300,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[5500,9000]

### offset_map48 — 48_Indoor_LowMixHigh
- 场景标签：Indoor_LowMixHigh（主类 Indoor，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.3059–0.6093；BpG 范围 0.6016–0.9547
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.2
- 触发条件：e_ratio[0,1]；BV[-9,-0.5]；CT[1500,5600]；IR[0,0.6]；Count[300,2400]；ColorCT[0,5400]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,5400]

### offset_map49 — 49_Night_extrem_low2
- 场景标签：Night_extrem_low2（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4247–0.6174；BpG 范围 0.6047–0.7647
- 目标坐标：(0.67, 0.37)，最近参考白点 A（距离 0.08868）；强拉至单点；权重 0.3
- 触发条件：e_ratio[0,1]；BV[-5,-0.5]；CT[1400,1800]；IR[0,0.8]；Count[300,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map50 — 50_Special_Indoor_Fire
- 场景标签：Special_Indoor_Fire（主类 Special，归类为室内场景）
- 几何覆盖：10 个顶点；RpG 范围 1.3455–1.8185；BpG 范围 0.2209–0.4625
- 目标坐标：(0.67, 0.42)，最近参考白点 A（距离 0.09082）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-8,4]；CT[1,5000]；IR[2,7]；Count[300,3072]；ColorCT[1,2800]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map51 — 51_Night_extrem_low3_y
- 场景标签：Night_extrem_low3_y（主类 Night，归类为夜景场景）
- 几何覆盖：7 个顶点；RpG 范围 1.2095–1.5723；BpG 范围 0.1751–0.3789
- 目标坐标：(0.84, 0.3)，最近参考白点 H（距离 0.11029）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-5,-0.5]；CT[1100,2100]；IR[0,998]；Count[300,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map52 — 52_spatial_Indoor_ColorCCT5600mixLowstats
- 场景标签：spatial_Indoor_ColorCCT5600mixLowstats（主类 spatial，归类为室内场景）
- 几何覆盖：4 个顶点；RpG 范围 0.6811–1.2627；BpG 范围 0.4349–0.7147
- 目标坐标：(0.46, 0.568)，最近参考白点 D50（距离 0.06416）；强拉至单点；权重 1
- 触发条件：e_ratio[0,1]；BV[3,5]；CT[2300,3500]；IR[0.01,0.1]；Count[600,1500]；ColorCT[5400,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map53 — 53_Special_indoor_MiddleMixHi_Redwall_20
- 场景标签：Special_indoor_MiddleMixHi_Redwall_20（主类 Special，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.4688–0.6037；BpG 范围 0.5629–0.6919
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[1,3]；CT[3800,4400]；IR[0.4,1.5]；Count[100,300]；ColorCT[4500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,4800]

### offset_map54 — 54_Special_indoor_MIdColorCCTwithLowstats2
- 场景标签：Special_indoor_MIdColorCCTwithLowstats2（主类 Special，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 0.6567–1.1316；BpG 范围 0.216–0.4918
- 目标坐标：(-0.03, 0)，最近参考白点 F（距离 0.78274）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0.5,3]；CT[2500,3500]；IR[0.15,0.35]；Count[800,2400]；ColorCT[4400,5500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map55 — 55_Special_GreenZone_indoor_EV2
- 场景标签：Special_GreenZone_indoor_EV2（主类 Special，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.2674–0.4594；BpG 范围 0.4259–0.5484
- 目标坐标：(0.38, 0.56)，最近参考白点 D50（距离 0.13758）；强拉至单点；权重 1
- 触发条件：e_ratio[0,1]；BV[1,3]；CT[3900,6000]；IR[0.01,0.2]；Count[600,1300]；ColorCT[4000,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map56 — 56_Special_huaweistore_gray
- 场景标签：Special_huaweistore_gray（主类 Special，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.7915–0.9844；BpG 范围 0.427–0.533
- 目标坐标：(-0.03, -0.03)，最近参考白点 F（距离 0.80163）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[5.5,7]；CT[1,3800]；IR[0,0.1]；Count[300,3000]；ColorCT[2500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map57 — 57_Special_indoor_market
- 场景标签：Special_indoor_market（主类 Special，归类为室内场景）
- 几何覆盖：10 个顶点；RpG 范围 0.5335–0.9145；BpG 范围 0.5537–0.8259
- 目标坐标：(0.5, 0.56)，最近参考白点 D50（距离 0.05128）；强拉至单点；权重 0.3
- 触发条件：e_ratio[0,1]；BV[2,7]；CT[3600,5000]；IR[0,0.15]；Count[600,3072]；ColorCT[3500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map58 — 58_Special_indoor_TL84Lab_Dmap16
- 场景标签：Special_indoor_TL84Lab_Dmap16（主类 Special，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 0.5109–0.7035；BpG 范围 0.4807–0.6204
- 目标坐标：(0.02, -0.02)，最近参考白点 F（距离 0.75725）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[1,4]；CT[3600,4600]；IR[0,1]；Count[1500,3072]；ColorCT[0,7000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map59 — 59_31_MixLight_HiMixLow_Dmap18
- 场景标签：MixLight_HiMixLow_Dmap18（主类 MixLight，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.5584–1.0469；BpG 范围 0.2836–0.5353
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[-0.5,6]；CT[3300,5500]；IR[0.22,0.5]；Count[600,1500]；ColorCT[4600,5700]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map60 — 60_32_MidMidxLow_Dmap12_food
- 场景标签：MidMidxLow_Dmap12_food（主类 MidMidxLow，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.666–1.1258；BpG 范围 0.2258–0.4579
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0,4]；CT[2400,3700]；IR[0.04,0.25]；Count[300,1800]；ColorCT[4000,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map61 — 61_33_MixLowMixHi_Dmap13
- 场景标签：MixLowMixHi_Dmap13（主类 MixLowMixHi，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.3306–0.7035；BpG 范围 0.5401–0.9272
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0,4]；CT[2500,4000]；IR[0.01,0.4]；Count[300,3072]；ColorCT[2000,3500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map62 — 62_34_MixLight_MidMixHi_Dmap14
- 场景标签：MixLight_MidMixHi_Dmap14（主类 MixLight，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.2542–0.5892；BpG 范围 0.625–0.9611
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0,4.5]；CT[3500,4700]；IR[0.01,0.25]；Count[600,800]；ColorCT[2500,4600]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map63 — 63_35_MixLight_MidMixHi_Dmap14
- 场景标签：MixLight_MidMixHi_Dmap14（主类 MixLight，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 0.4099–0.6875；BpG 范围 0.5597–0.6919
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.4
- 触发条件：e_ratio[0,1]；BV[0.8,4.8]；CT[4200,4700]；IR[0.01,0.25]；Count[200,700]；ColorCT[2500,4600]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map64 — 64__Special_indoor_green
- 场景标签：Special_indoor_green（主类 Special，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 0.3029–1.0652；BpG 范围 0.1285–0.4754
- 目标坐标：(0.54, 0.44)，最近参考白点 F（距离 0.06305）；强拉至单点；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-9,5]；CT[1500,4500]；IR[0,0.3]；Count[700,3072]；ColorCT[1000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map65 — 65_MidMixLow_Dmap19_oppostore1
- 场景标签：MidMixLow_Dmap19_oppostore1（主类 MidMixLow，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.7269–0.936；BpG 范围 0.3605–0.4909
- 目标坐标：(-0.08, 0.05)，最近参考白点 F（距离 0.79423）；整体位移；权重 0.3
- 触发条件：e_ratio[0,0.4]；BV[3.8,5]；CT[2800,4500]；IR[0.03,0.5]；Count[300,2300]；ColorCT[2800,5000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map66 — 66_MidMixLow_Dmap19_oppostore2
- 场景标签：MidMixLow_Dmap19_oppostore2（主类 MidMixLow，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.7129–0.936；BpG 范围 0.3746–0.4895
- 目标坐标：(-0.06, 0.05)，最近参考白点 F（距离 0.77756）；整体位移；权重 0.2
- 触发条件：e_ratio[0,0.6]；BV[5.5,8]；CT[2800,4500]；IR[0.03,0.5]；Count[800,2300]；ColorCT[3400,5000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map67 — 67_MixLight_MidMixHi_Dmap21_face
- 场景标签：MixLight_MidMixHi_Dmap21_face（主类 MixLight，归类为室内场景）
- 几何覆盖：4 个顶点；RpG 范围 0.3002–0.6035；BpG 范围 0.6173–0.9134
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0,4.5]；CT[3500,5000]；IR[0.01,0.3]；Count[200,3072]；ColorCT[2500,5400]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,5500]

### offset_map68 — 68_40_MixLight_indoor_specielgreen
- 场景标签：MixLight_indoor_specielgreen（主类 MixLight，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.7289–0.9524；BpG 范围 0.1468–0.2336
- 目标坐标：(0.9, 0.14)，最近参考白点 H（距离 0.20973）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[0,3]；CT[0,2800]；IR[0,0.5]；Count[1600,3072]；ColorCT[0,4000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map69 — 69_42_MixLight_indoor_blueclothes
- 场景标签：MixLight_indoor_blueclothes（主类 MixLight，归类为室内场景）
- 几何覆盖：10 个顶点；RpG 范围 0.2527–0.4363；BpG 范围 0.6133–0.8504
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.01
- 触发条件：e_ratio[0,1]；BV[0,5]；CT[1,4500]；IR[0,0.2]；Count[1,3072]；ColorCT[1,4500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,4500]

### offset_map70 — 70_60_Special_indoor_blue
- 场景标签：Special_indoor_blue（主类 Special，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4168–0.6012；BpG 范围 0.7581–0.9479
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.01
- 触发条件：e_ratio[0,1]；BV[4,9]；CT[3500,7000]；IR[0.05,0.3]；Count[600,3073]；ColorCT[1,4500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map71 — 71_IndoorScene_pureblue
- 场景标签：IndoorScene_pureblue（主类 IndoorScene，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.2065–0.358；BpG 范围 0.7612–0.9949
- 目标坐标：(0.45, 0.55)，最近参考白点 D50（距离 0.08387）；强拉至单点；权重 1
- 触发条件：e_ratio[0,1]；BV[-1,6]；CT[5500,12000]；IR[0.01,0.1]；Count[1800,3072]；ColorCT[3900,6500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map72 — 72_IndoorScene_purered
- 场景标签：IndoorScene_purered（主类 IndoorScene，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 1.6832–2.1684；BpG 范围 0.3699–0.5717
- 目标坐标：(0.45, 0.58)，最近参考白点 D50（距离 0.06553）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[-1.8,2.5]；CT[1100,5300]；IR[0.01,1]；Count[1000,3072]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map73 — 73_IndoorScene_starbuck_red
- 场景标签：IndoorScene_starbuck_red（主类 IndoorScene，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 1.1872–1.8214；BpG 范围 0.2338–0.3808
- 目标坐标：(0.82, 0.31)，最近参考白点 A（距离 0.10329）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[0.5,1.4]；CT[1300,2500]；IR[0.01,0.15]；Count[500,3072]；ColorCT[1,4000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map74 — 74_IndoorScene_LowMixExtreLow_14_y
- 场景标签：IndoorScene_LowMixExtreLow_14_y（主类 IndoorScene，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 1.0425–1.3652；BpG 范围 0.1895–0.365
- 目标坐标：(0.83, 0.37)，最近参考白点 A（距离 0.07686）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[0.5,4]；CT[2200,2600]；IR[0,2]；Count[400,1500]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map75 — 75_IndoorScene_starbuck2_1
- 场景标签：IndoorScene_starbuck2_1（主类 IndoorScene，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 1.0062–1.3044；BpG 范围 0.2541–0.3636
- 目标坐标：(0.87, 0.3)，最近参考白点 H（距离 0.08393）；强拉至单点；权重 0.6
- 触发条件：e_ratio[0,1]；BV[0.5,2]；CT[1500,2200]；IR[0.01,0.2]；Count[500,2100]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map76 — 76_indoorScene_HighMixLow_window
- 场景标签：indoorScene_HighMixLow_window（主类 indoorScene，归类为室内场景）
- 几何覆盖：13 个顶点；RpG 范围 0.638–1.2869；BpG 范围 0.1622–0.4782
- 目标坐标：(-0.06, 0.01)，最近参考白点 F（距离 0.80057）；整体位移；权重 0.3
- 触发条件：e_ratio[0,1]；BV[2,4]；CT[2500,3700]；IR[0.5,999]；Count[1,3072]；ColorCT[4800,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map77 — 77_indoorScene_HighMixLow_window_face
- 场景标签：indoorScene_HighMixLow_window_face（主类 indoorScene，归类为室内场景）
- 几何覆盖：13 个顶点；RpG 范围 0.638–1.2869；BpG 范围 0.1622–0.4782
- 目标坐标：(-0.04, 0.01)，最近参考白点 F（距离 0.78454）；整体位移；权重 0.3
- 触发条件：e_ratio[0,1]；BV[2,4]；CT[2500,3700]；IR[0.5,999]；Count[1,1500]；ColorCT[4800,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[4300,6000]

### offset_map78 — 78_MixLowMixHi_Dmap13_Face1
- 场景标签：MixLowMixHi_Dmap13_Face1（主类 MixLowMixHi，归类为室外场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3207–0.6132；BpG 范围 0.5953–0.873
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0,4]；CT[2500,4500]；IR[0.1,4]；Count[200,3072]；ColorCT[2000,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[3400,3800]

### offset_map79 — 79_100_indoor_red_out3000k
- 场景标签：indoor_red_out3000k（主类 indoor，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 1.6861–2.1772；BpG 范围 0.3327–0.5203
- 目标坐标：(0.72, 0.35)，最近参考白点 A（距离 0.05476）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-6,5]；CT[0,1800]；IR[0.5,2]；Count[200,3072]；ColorCT[3000,4500]；DiffCT[0,9000]；Y[0,254]；FaceCT[0,9000]

### offset_map80 — 80_69_IndoorScene_extremeLowcct_Redwall
- 场景标签：IndoorScene_extremeLowcct_Redwall（主类 IndoorScene，归类为室内场景）
- 几何覆盖：7 个顶点；RpG 范围 1.2458–1.7303；BpG 范围 0.2399–0.3824
- 目标坐标：(0.84, 0.335)，最近参考白点 H（距离 0.10091）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[2,5]；CT[1100,2000]；IR[0.01,7]；Count[1000,3072]；ColorCT[1,5000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map81 — 81_70_IndoorScene_indoor_NightLight
- 场景标签：IndoorScene_indoor_NightLight（主类 IndoorScene，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 1.2692–1.6069；BpG 范围 0.1509–0.2452
- 目标坐标：(0.66, 0.36)，最近参考白点 A（距离 0.10104）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[2,5]；CT[1000,2000]；IR[0,0.4]；Count[400,3072]；ColorCT[2500,4000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map82 — 82_IndoorScene_pureblue_ocean
- 场景标签：IndoorScene_pureblue_ocean（主类 IndoorScene，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.1912–0.3064；BpG 范围 0.8965–1.314
- 目标坐标：(0.415, 0.608)，最近参考白点 D50（距离 0.09295）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[-1,12]；CT[9000,12000]；IR[0.01,0.15]；Count[1000,3072]；ColorCT[5500,10000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map83 — 83_44_MixLight_indoor_green_Dmap17
- 场景标签：MixLight_indoor_green_Dmap17（主类 MixLight，归类为室内场景）
- 几何覆盖：6 个顶点；RpG 范围 0.4121–0.6133；BpG 范围 0.3926–0.5974
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[1,1]；BV[0.5,4]；CT[3200,5000]；IR[0,0.4]；Count[300,2000]；ColorCT[3000,6600]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map84 — 84_43_MixLight_indoor_bar
- 场景标签：MixLight_indoor_bar（主类 MixLight，归类为室内场景）
- 几何覆盖：12 个顶点；RpG 范围 0.3367–0.9577；BpG 范围 0.759–1.5308
- 目标坐标：(0.51, 0.54)，最近参考白点 D50（距离 0.0707）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[4500,12000]；IR[0,0.8]；Count[300,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map85 — 85_indoor_ExtremeLow_CCT_Wood_y
- 场景标签：indoor_ExtremeLow_CCT_Wood_y（主类 indoor，归类为室内场景）
- 几何覆盖：12 个顶点；RpG 范围 1.0506–1.366；BpG 范围 0.1862–0.3838
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-2,3]；CT[1500,3100]；IR[0,2]；Count[500,2100]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map86 — 86_MixLight_indoor_green2_Dmap17
- 场景标签：MixLight_indoor_green2_Dmap17（主类 MixLight，归类为室内场景）
- 几何覆盖：10 个顶点；RpG 范围 0.6567–0.893；BpG 范围 0.271–0.4072
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-0.5,4]；CT[0,2800]；IR[0,1]；Count[300,2000]；ColorCT[1,5500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map87 — 87_IndoorScene_starbuck2_2
- 场景标签：IndoorScene_starbuck2_2（主类 IndoorScene，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 1.0062–1.3044；BpG 范围 0.2541–0.3636
- 目标坐标：(0.74, 0.35)，最近参考白点 A（距离 0.0442）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-2,2]；CT[2400,3000]；IR[0.01,0.2]；Count[500,2100]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map88 — 88_56_Special_huaweistore_low
- 场景标签：Special_huaweistore_low（主类 Special，归类为室内场景）
- 几何覆盖：5 个顶点；RpG 范围 0.9477–1.2986；BpG 范围 0.2486–0.3871
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[5.5,7]；CT[1,3800]；IR[0,0.1]；Count[500,2000]；ColorCT[1,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,1000]

### offset_map89 — 89_MidMidxLow_Face
- 场景标签：MidMidxLow_Face（主类 MidMidxLow，归类为室外场景）
- 几何覆盖：7 个顶点；RpG 范围 0.7222–1.281；BpG 范围 0.1647–0.4579
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0.5,6.5]；CT[2400,3800]；IR[0.05,0.25]；Count[300,2000]；ColorCT[3000,5500]；DiffCT[1,9000]；Y[1,254]；FaceCT[3300,6000]

### offset_map90 — 90_MixLight_HiMixLow_Face
- 场景标签：MixLight_HiMixLow_Face（主类 MixLight，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.5584–1.0469；BpG 范围 0.2501–0.535
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.3
- 触发条件：e_ratio[0,1]；BV[1,6]；CT[3300,5500]；IR[0.04,0.6]；Count[600,2500]；ColorCT[2800,5700]；DiffCT[1,9000]；Y[1,254]；FaceCT[5100,9000]

### offset_map91 — 91_33_MixLowMixHi_Face2
- 场景标签：MixLowMixHi_Face2（主类 MixLowMixHi，归类为室外场景）
- 几何覆盖：9 个顶点；RpG 范围 0.3342–0.8315；BpG 范围 0.4021–0.8572
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[0.5,5]；CT[2500,4500]；IR[0.01,1]；Count[300,3072]；ColorCT[2000,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,3400]

### offset_map92 — 92_indoor_pureyellow_1
- 场景标签：indoor_pureyellow_1（主类 indoor，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.9793–1.1814；BpG 范围 0.2125–0.3226
- 目标坐标：(0.8, 0.32)，最近参考白点 A（距离 0.0836）；强拉至单点；权重 1
- 触发条件：e_ratio[0,0.15]；BV[0.5,4]；CT[0,2000]；IR[0,0.2]；Count[2200,3073]；ColorCT[0,7000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map93 — 93_indoor_pureyellow_2
- 场景标签：indoor_pureyellow_2（主类 indoor，归类为室内场景）
- 几何覆盖：8 个顶点；RpG 范围 0.8192–1.0383；BpG 范围 0.2967–0.3902
- 目标坐标：(-0.05, 0.03)，最近参考白点 F（距离 0.78074）；整体位移；权重 1
- 触发条件：e_ratio[0,0.15]；BV[0.5,4]；CT[0,2700]；IR[0,0.2]；Count[2200,3073]；ColorCT[0,7000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map94 — 94_Night_extrem_low
- 场景标签：Night_extrem_low（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4247–0.6174；BpG 范围 0.6047–0.7647
- 目标坐标：(1.02, 0.3)，最近参考白点 H（距离 0.09191）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[1400,2600]；IR[1.5,5]；Count[200,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map95 — 95_MixLight_indoor_pink
- 场景标签：MixLight_indoor_pink（主类 MixLight，归类为室内场景）
- 几何覆盖：9 个顶点；RpG 范围 0.4796–0.9467；BpG 范围 0.6429–1.1004
- 目标坐标：(0.415, 0.73)，最近参考白点 D65（距离 0.04223）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[4,8]；CT[4000,12000]；IR[0,1.5]；Count[1100,3072]；ColorCT[4500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map96 — 96_Night_Campfire
- 场景标签：Night_Campfire（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 1.0038–1.4423；BpG 范围 0.359–0.6288
- 目标坐标：(0.74, 0.42)，最近参考白点 A（距离 0.03304）；强拉至单点；权重 0.2
- 触发条件：e_ratio[0,1]；BV[-7,-2]；CT[0,2800]；IR[0,20]；Count[400,1500]；ColorCT[2800,3000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map97 — 97_Night_extrem_low1_y
- 场景标签：Night_extrem_low1_y（主类 Night，归类为夜景场景）
- 几何覆盖：4 个顶点；RpG 范围 1.212–1.368；BpG 范围 0.2501–0.3604
- 目标坐标：(0.88, 0.31)，最近参考白点 H（距离 0.07015）；强拉至单点；权重 0.6
- 触发条件：e_ratio[0,1]；BV[-8,0.5]；CT[1100,2700]；IR[0,998]；Count[500,1500]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map98 — 98_Night_pure_sand
- 场景标签：Night_pure_sand（主类 Night，归类为夜景场景）
- 几何覆盖：6 个顶点；RpG 范围 0.5615–0.6689；BpG 范围 0.4484–0.5442
- 目标坐标：(0.48, 0.49)，最近参考白点 F（距离 0.10535）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-1,1]；CT[1500,12000]；IR[1,998]；Count[2200,3072]；ColorCT[5000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map99 — 99_Night_sunsetblue_moment
- 场景标签：Night_sunsetblue_moment（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.447–0.893；BpG 范围 0.3031–0.625
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[4500,12000]；IR[0,998]；Count[400,1500]；ColorCT[4200,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map100 — 100_Night_skyMixgreen
- 场景标签：Night_skyMixgreen（主类 Night，归类为夜景场景）
- 几何覆盖：10 个顶点；RpG 范围 0.3322–0.6543；BpG 范围 0.3769–0.6985
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.01
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[4000,12000]；IR[0,998]；Count[500,3072]；ColorCT[5500,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map101 — 101_Night_special_green_HiCS_CCT
- 场景标签：Night_special_green_HiCS_CCT（主类 Night，归类为夜景场景）
- 几何覆盖：4 个顶点；RpG 范围 0.4131–0.6499；BpG 范围 0.5049–0.6774
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,1]；CT[5300,12000]；IR[0,998]；Count[300,3072]；ColorCT[6000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map102 — 102_Special_night_purered
- 场景标签：Special_night_purered（主类 Special，归类为夜景场景）
- 几何覆盖：4 个顶点；RpG 范围 1.5657–2.48；BpG 范围 0.2409–0.488
- 目标坐标：(0.435, 0.568)，最近参考白点 D50（距离 0.08448）；强拉至单点；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-2,3]；CT[1400,1800]；IR[0.01,0.2]；Count[100,3072]；ColorCT[1,4000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map103 — 103_Night_MidMixLow1
- 场景标签：Night_MidMixLow1（主类 Night，归类为夜景场景）
- 几何覆盖：4 个顶点；RpG 范围 0.6309–1.1493；BpG 范围 0.2032–0.4858
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[2500,3300]；IR[0.25,998]；Count[200,2200]；ColorCT[3500,5000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map104 — 104_Night_MidMixLow
- 场景标签：Night_MidMixLow（主类 Night，归类为夜景场景）
- 几何覆盖：4 个顶点；RpG 范围 0.7155–1.1493；BpG 范围 0.2032–0.4454
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-0.5,1]；CT[2500,3300]；IR[0.02,0.25]；Count[200,2200]；ColorCT[2900,4500]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map105 — 105_Night_greysky
- 场景标签：Night_greysky（主类 Night，归类为夜景场景）
- 几何覆盖：6 个顶点；RpG 范围 0.3444–0.5812；BpG 范围 0.6081–0.8025
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.7
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[4000,6000]；IR[0,0.5]；Count[400,1500]；ColorCT[0,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,100]

### offset_map106 — 106_Night_greysky3
- 场景标签：Night_greysky3（主类 Night，归类为夜景场景）
- 几何覆盖：5 个顶点；RpG 范围 0.5117–0.6988；BpG 范围 0.5069–0.6453
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[2300,2900]；IR[0.01,0.15]；Count[200,600]；ColorCT[0,3000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map107 — 107_Night_candle
- 场景标签：Night_candle（主类 Night，归类为夜景场景）
- 几何覆盖：5 个顶点；RpG 范围 1.3252–1.7151；BpG 范围 0.1633–0.2955
- 目标坐标：(0.88, 0.33)，最近参考白点 H（距离 0.06236）；强拉至单点；权重 0.4
- 触发条件：e_ratio[0,1]；BV[-8,0]；CT[1400,1650]；IR[0,998]；Count[1,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map108 — 108_Night_special_HighMixMid
- 场景标签：Night_special_HighMixMid（主类 Night，归类为夜景场景）
- 几何覆盖：6 个顶点；RpG 范围 0.6543–0.9429；BpG 范围 0.3333–0.5051
- 目标坐标：(-0.1, 0.07)，最近参考白点 F（距离 0.80053）；整体位移；权重 0.3
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[3500,4000]；IR[0,0.2]；Count[1000,1300]；ColorCT[0,3500]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,3000]

### offset_map109 — 109_Nightbluesky_green
- 场景标签：Nightbluesky_green（主类 Nightbluesky，归类为夜景场景）
- 几何覆盖：10 个顶点；RpG 范围 0.1977–0.4205；BpG 范围 0.4052–0.6664
- 目标坐标：(0.345, 0.7)，最近参考白点 D75（距离 0.11579）；强拉至单点；权重 0.5
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[4600,7000]；IR[0,998]；Count[1700,3072]；ColorCT[0,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map110 — 110_Night_HiMixLow
- 场景标签：Night_HiMixLow（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4958–0.9408；BpG 范围 0.2865–0.5815
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,-0.5]；CT[3500,12000]；IR[0,998]；Count[300,3072]；ColorCT[4000,12000]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map111 — 111_Night_HighMixMid
- 场景标签：Night_HighMixMid（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.4965–0.8499；BpG 范围 0.3408–0.5877
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.15
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[3500,12000]；IR[0,998]；Count[700,1300]；ColorCT[5400,6800]；DiffCT[1,9000]；Y[1,254]；FaceCT[0,9000]

### offset_map112 — 112_Night_HighMixLow_Face2
- 场景标签：Night_HighMixLow_Face2（主类 Night，归类为夜景场景）
- 几何覆盖：6 个顶点；RpG 范围 0.5671–0.831；BpG 范围 0.3341–0.5362
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,-1]；CT[4000,4600]；IR[0,998]；Count[400,1300]；ColorCT[0,12000]；DiffCT[0,9000]；Y[1,254]；FaceCT[6200,9000]

### offset_map113 — 113_Night_HighMixlow_Face1
- 场景标签：Night_HighMixlow_Face1（主类 Night，归类为夜景场景）
- 几何覆盖：7 个顶点；RpG 范围 0.8038–1.1492；BpG 范围 0.1672–0.4291
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 1
- 触发条件：e_ratio[0,0]；BV[-5,0.5]；CT[2300,3100]；IR[0,998]；Count[500,1800]；ColorCT[0,5700]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,5000]

### offset_map114 — 114_Night_HighMixlow_Face
- 场景标签：Night_HighMixlow_Face（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.6075–1.006；BpG 范围 0.2797–0.5015
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[-5,0.5]；CT[3300,5500]；IR[0,998]；Count[300,2000]；ColorCT[0,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,9000]

### offset_map115 — 115_Night_LowMixHigh_Face
- 场景标签：Night_LowMixHigh_Face（主类 Night，归类为夜景场景）
- 几何覆盖：8 个顶点；RpG 范围 0.2419–0.5723；BpG 范围 0.5235–0.9303
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 1
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[1500,12000]；IR[0,3]；Count[300,1400]；ColorCT[0,6000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,5000]

### offset_map116 — 116_Night_LowMixHigh_Face1
- 场景标签：Night_LowMixHigh_Face1（主类 Night，归类为夜景场景）
- 几何覆盖：10 个顶点；RpG 范围 0.2449–0.7823；BpG 范围 0.3828–0.9352
- 目标坐标：(0, 0)，最近参考白点 F（距离 0.75939）；整体位移；权重 0.1
- 触发条件：e_ratio[0,1]；BV[-5,0]；CT[2500,3400]；IR[0,998]；Count[300,500]；ColorCT[0,3000]；DiffCT[1,9000]；Y[1,254]；FaceCT[1500,3000]

## 室内 / 室外 / 夜景整体规律

### 总体规律综述

#### 户外策略
蓝天与高亮日景（offset_map01–09）以 0.26–0.48 的 RpG、0.62–1.15 的 BpG 包络锁定偏蓝统计点，统一强拉到 D50 左右，确保在 7.3–15 EV、5000–12000K 的高照度场景下迅速回到日光白点，其中 map03 额外将权重提升到 0.5 对应晴天强光。

低光蓝天与雪景（offset_map04–07、15、17）改用位移映射，offset 在 RpG 正向、BpG 负向（例如 +0.01/-0.035、+0.032/-0.065），显著提升 R 增益压低 B 增益以暖化画面，并通过 e_ratio=0、bv 0–8 等约束只在高蓝偏、纹理稀少的低光天空中生效。

“GreenZone”“OutdoorScene”“sunset” 系列（offset_map16–43）混合使用强拉与位移：例如 map19 拉向 F 白点、map20/24 落在 D50/D65 附近、map30–37 保持 offset=0 只凭权重调节；同时通过 IR、count、faceCtemp 等门限拆分植被、天空、暮光与人脸场景，构成完整的户外链路。

#### 室内策略
典型室内/混合光（offset_map12、44、46、48）多采用 ml=65535 位移配合 0~几千 lux 的 count 与 0–4500K 的 ctemp 区间，在 offset 轻微负向 RpG、正向 BpG 下放缓暖色加成，适应酒吧、低照室内或高混光窗景。

MixLight/Special indoor（offset_map59–70）主要保持 offset=0 依赖统计权重，但针对 Oppo/Huawei 店铺、绿植灯箱等特殊场景设置低 IR、count 约束，并辅以少量强拉（如 map64、68）直接拉向 F/H 以抑制偏绿或偏青灯光。

纯色/品牌门店（offset_map71–95）结合强拉与位移处理蓝、红、黄等极端色块：map71/72 拉回 D50，map87/92 定位在 A 点抑制暖调，map93 通过 (-0.05, +0.03) 平移维持黄光质感；同时限制 count≥1800 或设置 faceCtemp 条件，确保在大量纯色或人脸的特定照明下触发。

#### 夜景策略
夜景低照（offset_map49–52、94–101）普遍允许 bv -7～0、ctemp 0–3100K，权重 0.1–0.4 配合强拉到 A/H 等暖点，快速抑制钠灯、营火的偏色；其中 map94/96 分别靠近 H/A 点纠正极暖色温。

夜间混光/高混光（offset_map103–111）以 offset=0 的位移配合 IR、faceCtemp 分段控制，允许适度蓝绿分量保留环境氛围，同时权重 0.1–0.4 抑制剧烈偏移。

夜景人脸专用（offset_map112–116）设置 faceCtemp 1500–9000、count≤2000 等门限，并以高权重位移或保持 offset=0，确保夜间肖像不过度偏色；其中 map113/114 在 e_ratio=0、ctemp 2300–5500K 下针对暗部红黄灯光矫正。

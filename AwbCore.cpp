int AwbCore::CalcWhiteBalanceGain( int camId)
{
    int pos;
    // Stats Precision
    int start = m_priv.statsPrecision.startPos;
    int step  = m_priv.statsPrecision.precision;
    CAM_ALGO_LOG_VERBOSE("CalcWhiteBalanceGain: step =%d",step);
    float OriCTempWeight = 1.0f;
    float OffsetTargetCTempWeight = 1.0f;
    float DistTargetCTempWeight = 1.0f;

    float OriBlockWeight = 1.0f;
    float OffsetTargetBlockWeight = 1.0f;
    float DistTargetBlockWeight = 1.0f;

    float OriIrWeight = 1.0f;
    float OffsetTargetIrWeight = 1.0f;
    float DistTargetIrWeight = 1.0f;

    float weightYLevel = 1.0f;
    float CPerBlockWeight = 0.0f;
    float distWeight = 0.0f;
    float integralWeight = 0.0f;
    int   intoMapCount = 0;
    float integralWeightNoMap = 0.0f;
    float stdRpg = 0.0f;
    float stdBpg = 0.0f;
    float cVar = 0.0f;

    SOpAwb_ColorSpace    integral = { 0.0f, 0.0f };
    SOpAwb_ColorSpace    integralNoMap = { 0.0f, 0.0f };
    SOpAwb_ColorSpace    block = { 0.0f, 0.0f };
    SOpAwb_ColorSpace    blockDistTarget = { 0.0f, 0.0f };

    int cntRow = m_priv.stats.info.row;
    int cntCol = m_priv.stats.info.col;
    SOpAwbCore_SubPlusOffsetTable spOffsetTable[OPAWB_DETECTMAP_TARGET_NUM];
    int blockPixcels = m_priv.stats.info.blockHeight * m_priv.stats.info.blockWidth >> 2;
    int bitShift = m_priv.stats.info.bitDepth - 8;
    SOpAwb_ColorSpaceMapInfo* csMapInfo = &(m_priv.info.tuningParam.WBGainParam.mapInfo);
    SOp_BlockStatisticsRGB* stats = m_priv.stats.stats;

    const float edge_ratio = ((cntRow * cntCol) == 0) ? 0 : ((float)m_priv.stats.info.edgeCnt/(float)(cntRow * cntCol));
    m_priv.info.currentFrame.eRatio = edge_ratio;

    SOpAwb_ColorSpace    totalTmp = { 0.0f, 0.0f };
    ALGO_MEMSET(spOffsetTable, 0, sizeof(spOffsetTable));
    for(int i = 0; i < OPAWB_DETECTMAP_TARGET_NUM; i++) {
        spOffsetTable[i].targetMapNo = -1;
    }

    SOpAwbCore_Cluster dCluster[OPAWB_DETECTMAP_TARGET_NUM] = {{0}};
    unsigned short target_cluster_index[OPAWB_DETECTMAP_TARGET_NUM+1] ={0};
    int detectmapPointOffsetmapNum = 4;
    SCIE_COLOR_CCT resultCCt;
    int mapSize = m_pTuning->modeParam.pAwbTuningParam->opAwb_TblOffsetMapNum;

    // malloc dynamic memory
    if(mapSize <= 0)
    {
        CAM_ALGO_LOG_ERROR("Memory allocation size error");
        return eOp_StatusNG;
    }
    if(!m_priv.pFrameData) {
        m_priv.pFrameData = (FrameData*)ALGO_MEM_CALLOC(1, sizeof(FrameData));
        CHECK_PTR_RET(m_priv.pFrameData);
    }
    if(!m_priv.pMapStats) {
        m_priv.pMapStats = (SOpOffsetMapTem*)ALGO_MEM_CALLOC(1, sizeof(SOpOffsetMapTem) * mapSize);
        CHECK_PTR_RET(m_priv.pMapStats);
    }

    //set detectmap clusterinfo
    DetectMapCluster(dCluster, target_cluster_index,detectmapPointOffsetmapNum);

    FrameData* pFrameData = m_priv.pFrameData;
    pFrameData->needToProcessStatsSize = 0;
    pFrameData->fMaxDist = sqrt(csMapInfo->length.width * csMapInfo->length.width + csMapInfo->length.height * csMapInfo->length.height);
    pFrameData->fMaxDistReop = 1.0f / pFrameData->fMaxDist;
    CIE_COLOR_XYZ *xyzData = (CIE_COLOR_XYZ *)(pFrameData->pureColorData.xyzData);// allocated in init step
    bool enPureColor = m_pTuning->modeParam.pAwbTuningParam->opAwb_PureColorDetParam.pureDetectEn;
    if(m_priv.info.purePropEn > 0) {// force use prop value
        enPureColor = m_priv.info.purePropEn == 1 ? true : false;
    }

    CAM_ALGO_LOG_VERBOSE("correctCoefRpG %f, correctCoefBpG %f, enPureColor:%d",
        m_priv.info.unitDiff.adjustWbg.adjust_wbg_rgain, m_priv.info.unitDiff.adjustWbg.adjust_wbg_bgain, enPureColor);

    CheckBaseBoundaryMapIsRange();

    CalcSgwInfo(camId);

    CalcTriggerCtemp();

    // skip frame process
    bool isSkipFrame = CalcSkipFrameInfo(camId);
    if(isSkipFrame) {
        return eOp_StatusOK;
    }

    if (enPureColor) {// only for debug
        if ( (REAR_MAIN_CAMERA_ID == camId || REAR_WIDE_CAMERA_ID == camId || REAR_TELE_CAMERA_ID == camId || REAR_TELE2_CAMERA_ID == camId)) {
        /*********************************PURE*COLOR*DECTECT*START*********************************/
        //PureColor Detection start
        float maxrate = 0.0;
        int idx = 0;
#if USE_PURE_COLOR_DEC_OPT
        if (m_priv.info.currentFrame.auxCamStatus.isAuxCam && (camId == 0))
        {
            if((m_priv.info.frameNum % 10) == 0)
            {
                CalcPureColorDetection(camId, &idx, &maxrate);
            }
        }
        else
        {
            if((m_priv.info.frameNum % 2) == 0)
            {
                CalcPureColorDetection(camId, &idx, &maxrate);
            }
        }
#else // USE_PURE_COLOR_DEC_OPT
        CalcPureColorDetectionOri(camId, &idx, &maxrate);
#endif // USE_PURE_COLOR_DEC_OPT
        }
    } else {
        CAM_ALGO_LOG_ERROR("awb.pure.enable = 0, bypass oplus pure color algo.");
    }

    // reset frame info
    ResetFrameInfo();

    const UI32 flagDetectMapScreen = StatsDetectMapScreenGetFlag();
    const Bits128 flagCalcOffsetMapCnt = CalcOffsetMapCntGetFlag(edge_ratio);

    StatsMapScreen(flagDetectMapScreen, flagCalcOffsetMapCnt);

    //detect map
    OffsetMapAdjust(spOffsetTable, dCluster, target_cluster_index,detectmapPointOffsetmapNum);

    SOpOffsetMapTem* sOpMapStats = m_priv.pMapStats;
    CalcOffsetMapConfidence(sOpMapStats, spOffsetTable, edge_ratio);  //isRange set
    CalcOffsetDynamicAdjust(sOpMapStats, spOffsetTable, edge_ratio);  //adjust map's offset & weight using dynamic trigger
    Bits128 sOpMapStatsIsRangeFlag = {0};
    update128OffsetMapStatusIsRangeFlag(&sOpMapStatsIsRangeFlag, sOpMapStats, m_pTuning->modeParam.pAwbTuningParam->opAwb_TblOffsetMapNum);

    CalcWhiteBlanceGainStep6(edge_ratio, sOpMapStats, &sOpMapStatsIsRangeFlag);

    for(int i=0; i < OPAWB_BASEMAP_SHEET_NUM; i++)
    {
        CAM_ALGO_LOG_VERBOSE("baseMapCount[%d] %d", i, m_priv.info.currentFrame.baseMapCount[i]);
    }

    CalcBaseMapConfidence(sOpMapStats, edge_ratio);   ////isRange set
    updateBaseMapStatusIsRangeFlag(&sOpMapStatsIsRangeFlag, sOpMapStats);

    CalcIrFinalWeightCommon(pFrameData);
    const int needToProcessStatsSize = pFrameData->needToProcessStatsSize;
    float* yLvWeiMap = m_priv.info.tuningParam.WBGainParam.yLevelWeight;
    const float blockPixcels_Reop = 1.0f / blockPixcels;
    int opAwbCtempWeightV2Enable = m_pTuning->modeParam.pAwbTuningParam->opAwbCtempWeightV2Enable;
    auto& weightPtr = m_priv.info.tuningParam.WBGainParam.ctempWeight;

    for(int index = 0; index < needToProcessStatsSize; ++index)
    {
        block = pFrameData->pBlock[index];
        TargetBlock *blockOffsetTarget = pFrameData->pOffsetTargetBlock + index;
        blockDistTarget = pFrameData->pDistTargetBlock[index];
        const UI32 blockMixTargetIndex = pFrameData->pMixTargetBlockIndex[index];
        distWeight = pFrameData->pDistWeight[index];
        pos = pFrameData->pPos[index];
        SOp_BlockStatisticsRGB* currentStats = stats + pos;
        const UI32 csmapIndex = pFrameData->pBlockMapIndex[index];
        const UI32 blockDistTarget_MapIndex = GetCsMapIndex2(csMapInfo, blockDistTarget);
        const UI32 boundaryMapDot_blockDistTarget = (((UI32)(GetBoundaryMapDot(blockDistTarget_MapIndex) >> 32)) & sOpMapStatsIsRangeFlag.data[0]);
        const Bits128 boundaryMapDot_block = bitsAndBits128(&pFrameData->pBoundaryMapDot_Block[index], &sOpMapStatsIsRangeFlag);
        const Bits128 distWeightMapDot_block = bitsAndBits128(&pFrameData->pDistWeightMapDot_Block[index], &sOpMapStatsIsRangeFlag);

        float fOriBaseW, fOffsetTargetBaseW, fDistTargetBaseW;
        float fOffsetConfience, fDistConfience;
        float fOffsetWeight, fDistMapWeight;
        float fOffsetTargetWeight, fDistTargetWeight, fOriWeight;
        float oriConfidenceMin = 1.0;
        float tempRpG = 0;
        float tempBpG = 0;
        float tempWeight = 0;
        //////////////////////////////////
        if(opAwbCtempWeightV2Enable)
        {
            weightPtr.tableHigh = pFrameData->pDuvCtempWeightHigh[index];
            weightPtr.tableLow = pFrameData->pDuvCtempWeightLow[index];
        }
        OriCTempWeight = CalcTargetCTempWeightMap(GetCsMapIndex2(csMapInfo, block));
        DistTargetCTempWeight = CalcTargetCTempWeightMap(blockDistTarget_MapIndex);

        const CTEMP ctempBlock = CalcCorrelateColorTemperature2(csmapIndex);
        const CTEMP ctempBlockDistTarget = CalcCorrelateColorTemperature2(blockDistTarget_MapIndex);
        OriIrWeight = CalcIrFinalWeightOpt(ctempBlock);
        DistTargetIrWeight = CalcIrFinalWeightOpt(ctempBlockDistTarget);
        weightYLevel = yLvWeiMap[(unsigned int)(currentStats->Y)];//Calc YLevelWeight Map
        CPerBlockWeight = (float)(currentStats->C) * blockPixcels_Reop;
        OriBlockWeight = OriCTempWeight * OriIrWeight * weightYLevel * CPerBlockWeight;
        DistTargetBlockWeight = DistTargetCTempWeight * DistTargetIrWeight * weightYLevel * CPerBlockWeight;
        m_priv.info.currentFrame.fStatsWeight[pos] = OriBlockWeight;
        MergeDistWeightResult tmpMergeDistWeightResult = GetDistMapConfidenceTargetWeight(distWeightMapDot_block, sOpMapStats);
        fDistConfience = tmpMergeDistWeightResult.confidence;
        fDistMapWeight = tmpMergeDistWeightResult.targetWeight;
        fOriBaseW = GetBaseMapConfidenceWeight32(boundaryMapDot_block.data[0], sOpMapStats);
        fDistTargetBaseW = GetBaseMapConfidenceWeight32(boundaryMapDot_blockDistTarget, sOpMapStats);
        fDistTargetWeight = fDistMapWeight * distWeight * fDistConfience * fDistTargetBaseW * DistTargetBlockWeight;
        //////////////////////////////////
        for(int i = 0; i < blockOffsetTarget->InOffsetMapNum; i++)
        {
            if(blockOffsetTarget->inMapYlevelRange[i] == false)
            {
                continue;
            }
            const int offsetMapIndex = blockOffsetTarget->OffsetMapIndex[i];
            SOpAwb_ColorSpace offsetMapTarget = blockOffsetTarget->Block[i];
            const UI32 offsetMapTarget_MapIndex = GetCsMapIndex2(csMapInfo, offsetMapTarget);
            OffsetTargetCTempWeight = CalcTargetCTempWeightMap(offsetMapTarget_MapIndex);
            //ir Weight
            const CTEMP offsetMapTargetCTEMP = CalcCorrelateColorTemperature2(offsetMapTarget_MapIndex);
            OffsetTargetIrWeight = CalcIrFinalWeightOpt(offsetMapTargetCTEMP);
            OffsetTargetBlockWeight = OffsetTargetCTempWeight * OffsetTargetIrWeight * weightYLevel * CPerBlockWeight;
            fOffsetConfience = sOpMapStats[offsetMapIndex].SelectConfidence;
            fOffsetWeight = sOpMapStats[offsetMapIndex].totalWeight;
            const UI32 boundaryMapDot_offsetMapTarget = ((UI32)(GetBoundaryMapDot(offsetMapTarget_MapIndex) >> 32)) & sOpMapStatsIsRangeFlag.data[0];
            fOffsetTargetBaseW = GetBaseMapConfidenceWeight(boundaryMapDot_offsetMapTarget, sOpMapStats);
            fOffsetTargetWeight = fOffsetWeight * fOffsetConfience * fOffsetTargetBaseW * OffsetTargetBlockWeight;
            if((1 - fOffsetConfience) > 0 && (distWeight - distWeight * fDistConfience) > 0)
            {
                fOriWeight = (OP_AWB_MIN((1 - fOffsetConfience), (distWeight - distWeight * fDistConfience))) * fOriBaseW * OriBlockWeight;
            }
            else
            {
                fOriWeight = (1 - fOffsetConfience + distWeight - distWeight * fDistConfience) * fOriBaseW * OriBlockWeight;
            }
            oriConfidenceMin = (oriConfidenceMin > fOriWeight)?fOriWeight:oriConfidenceMin;
            tempRpG += (offsetMapTarget.RpG * fOffsetTargetWeight + blockDistTarget.RpG * fDistTargetWeight);
            tempBpG += (offsetMapTarget.BpG * fOffsetTargetWeight + blockDistTarget.BpG * fDistTargetWeight);
            tempWeight += (fDistTargetWeight + fOffsetTargetWeight);
        }

        if(blockOffsetTarget->InOffsetMapNum == 0)//maybe in distmap
        {
            oriConfidenceMin = (1.0f + distWeight - distWeight * fDistConfience) * fOriBaseW * OriBlockWeight;
            tempRpG += (blockDistTarget.RpG * fDistTargetWeight);
            tempBpG += (blockDistTarget.BpG * fDistTargetWeight);
            tempWeight += (fDistTargetWeight);
        }

        if((tempWeight + oriConfidenceMin) > 0)
        {
            const UI32 boundaryMapDotH32_blockMixTarget = ((UI32)(GetBoundaryMapDot(blockMixTargetIndex) >> 32)) & sOpMapStatsIsRangeFlag.data[0];
            CalcFinalBaseMapCnt(boundaryMapDotH32_blockMixTarget);
        }

        CalcFinalOffsetMapCnt(boundaryMapDot_block, distWeightMapDot_block);


        integral.RpG += (tempRpG + block.RpG * oriConfidenceMin);
        integral.BpG += (tempBpG + block.BpG * oriConfidenceMin);
        integralWeight += (tempWeight + oriConfidenceMin);
        integralNoMap.RpG += (block.RpG * OriBlockWeight * fOriBaseW);
        integralNoMap.BpG += (block.BpG * OriBlockWeight * fOriBaseW);
        integralWeightNoMap += (OriBlockWeight * fOriBaseW);

        stdRpg = stdRpg + (block.RpG - m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.RpG) *
            (block.RpG - m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.RpG);
        stdBpg = stdBpg + (block.BpG - m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.BpG) *
            (block.BpG - m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.BpG);
    }

    for(int i=0; i < OPAWB_BASEMAP_SHEET_NUM; i++)
    {
        intoMapCount += m_priv.info.currentFrame.baseMapPlotCount[i];
        CAM_ALGO_LOG_VERBOSE("baseMapPlotCount2[%d] %d", i, m_priv.info.currentFrame.baseMapPlotCount[i]);
    }

    if (pFrameData->needToProcessStatsSize > 0){
        stdRpg = (stdRpg / needToProcessStatsSize) / m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.RpG;
        stdBpg = (stdBpg / needToProcessStatsSize) / m_priv.info.currentFrame.fallbackInfo.sgwInfo.SGW_gray.BpG;
    }

    m_priv.info.currentFrame.fallbackInfo.agwConfidenceInfo.cVar = (stdRpg + stdBpg) / 2;

    m_priv.info.currentFrame.fallbackInfo.agwConfidenceInfo.vaildCntRatio =
        ((cntRow * cntCol) == 0) ? 0 : ((float)intoMapCount / (float)(cntRow * cntCol));
    CAM_ALGO_LOG_VERBOSE("agwWeight vaildCntRatio %f, bv %f, cVar %f",
        m_priv.info.currentFrame.fallbackInfo.agwConfidenceInfo.vaildCntRatio,
        m_priv.info.currentFrame.fallbackInfo.bv,
        m_priv.info.currentFrame.fallbackInfo.agwConfidenceInfo.cVar);


    // Stats Precision
    m_priv.statsPrecision.startPos = 0;

    //Color temperature range specification WB invertibility
    if(m_priv.info.ctempRange.enable == true)
    {
        if(intoMapCount < m_priv.info.ctempRange.blockCount)
        {
            // Cleared various measurement results because it was not accepted
            integralWeight = 0.0f;
            integral.RpG = 0.0f;
            integral.BpG = 0.0f;
        }
        CAM_ALGO_LOG_VERBOSE("CTemp Range intoMapCount: %d, Stats RpG: %5.6f, BpG: %5.6f, Wei: %5.6f", intoMapCount, integral.RpG, integral.BpG, integralWeight);
    }
    if((JudgeLightSourceEstimation(m_priv.info.currentFrame.fallbackInfo.bv, intoMapCount) == false ) || ( integralWeight <= 0.0f ) || ( integral.RpG <= 0.0f ) || (integral.BpG <= 0.0f) )
    {//If it is outside WhiteMap or integration result is 0, WBGain can not be calculated, so use the previous frame WBGain
        CAM_ALGO_LOG_VERBOSE("use lastFrame intoMapCount(colorsenor reference): %d, Stats RpG: %5.6f, BpG: %5.6f, Wei: %5.6f", intoMapCount, integral.RpG, integral.BpG, integralWeight);
        m_priv.info.currentFrame.fallbackInfo.integral.RpG = 0.0f;
        m_priv.info.currentFrame.fallbackInfo.integral.BpG = 0.0f;
        m_priv.info.currentFrame.AGW_gray.RpG = 0.0f;
        m_priv.info.currentFrame.AGW_gray.BpG = 0.0f;
        m_priv.info.currentFrame.After_Face.RpG = 0.0f;
        m_priv.info.currentFrame.After_Face.BpG = 0.0f;
        m_priv.info.currentFrame.Mix_dayLight.RpG = 0.0f;
        m_priv.info.currentFrame.Mix_dayLight.BpG = 0.0f;
        m_priv.info.currentFrame.dayLightMixWeight = 0.0f;
        m_priv.info.currentFrame.agwNoMap.RpG = 0.0f;
        m_priv.info.currentFrame.agwNoMap.BpG = 0.0f;

        m_priv.info.currentFrame.fallbackInfo.ctemp = m_priv.info.lastFrame.ctemp;
        m_priv.info.currentFrame.fallbackInfo.cnvgWBGain = m_priv.info.lastFrame.cnvgWBGain;
        m_priv.info.currentFrame.integralWeight = 1.0f;
        m_priv.info.currentFrame.fallbackInfo.cnvgEst = m_priv.info.lastFrame.cnvgEst;

        CalcCSFinalConfidence(camId);

        if ((REAR_MAIN_CAMERA_ID == camId || REAR_WIDE_CAMERA_ID == camId || REAR_TELE_CAMERA_ID == camId || REAR_TELE2_CAMERA_ID == camId) &&
            OP_AWB_COLORSENSOR_MULTI_SPECTRUM == m_priv.info.currentFrame.sColorSensor.sensor_type)
        {
            //Calculate GSL Gain
            float gslGain[eOpAwb_BoundaryMapXYCnt] = { 1.0, 1.0 };
            if(m_priv.info.gslInfo.duvEnable){
                //float gslGainV2[eOpAwb_BoundaryMapXYCnt] = { 1.0, 1.0 };
                CalcGainScalingGainMapV2(gslGain);
            }else{
                CalcGainScalingGainMap(m_priv.info.currentFrame.csAlgoRet.rpg, m_priv.info.currentFrame.csAlgoRet.bpg, gslGain);
            }

            float csAlgoRpg = 0;
            float csAlgoBpg = 0;
            float targetRpg = 0;
            float targetBpg = 0;
            CTEMP targetCtemp = 0;
            csAlgoRpg = m_priv.info.currentFrame.csAlgoRet.rpg / (gslGain[0]+EPS);
            csAlgoBpg = m_priv.info.currentFrame.csAlgoRet.bpg / (gslGain[1]+EPS);
            targetCtemp = m_priv.info.currentFrame.fallbackInfo.ctemp * (1.0f - m_priv.info.currentFrame.csFinalRatio) + m_priv.info.currentFrame.csAlgoRet.cct * m_priv.info.currentFrame.csFinalRatio;

            CAM_ALGO_LOG_VERBOSE("agwWeight use lastFrame %f, ori csFinalRatio %f",
                m_priv.info.currentFrame.fallbackInfo.agwConfidenceInfo.finalAgwRatio,
                m_priv.info.currentFrame.csFinalRatio);

            CalcAgwCsMixWB(m_priv.info.currentFrame.fallbackInfo.cnvgEst.RpG, m_priv.info.currentFrame.fallbackInfo.cnvgEst.BpG,csAlgoRpg, csAlgoBpg, &targetRpg, &targetBpg, camId);

            SkinOutInit();
            if (m_pTuning->modeParam.pAwbTuningParam->opAwbFaceTuningParam.face_awb_enable && m_pIn != NULL && m_pIn->pFaceDetectionInfo != NULL &&
                (m_pIn->pFaceDetectionInfo->roi_count > 0 && m_pIn->pFaceDetectionInfo->roi_count < MAX_AWB_FACE_NUM))
            {
                // [set skincore frame info]
                BuildSkinCoreData();
                // [skincore exec]
                SubCoreProcess(&m_skinCoreIn, &m_skinCoreOut, SubAwbCoreTypeE::SKIN_CORE);
            }

            if (m_skinCoreOut.skinCoreOut.faceawb_is_confident){
                CAM_ALGO_LOG_VERBOSE("faceawb_weight %f final_face_wb_r_gain %f final_face_wb_b_gain %f, final_skin_cct %f",
                    m_skinCoreOut.skinCoreOut.faceawb_weight, m_skinCoreOut.skinCoreOut.final_face_wb_r_gain,
                    m_skinCoreOut.skinCoreOut.final_face_wb_b_gain, m_skinCoreOut.skinCoreOut.final_skin_cct);

                m_priv.info.currentFrame.faceAdjustConfidence =
                    CalcFaceAwbAdjustConfidence(&m_pTuning->modeParam.pAwbTuningParam->opAwb_FaceAwbAdjustParam,
                        m_skinCoreOut.skinCoreOut.faceawb_weight);

                targetRpg = (1 / m_skinCoreOut.skinCoreOut.final_face_wb_r_gain) * m_priv.info.currentFrame.faceAdjustConfidence +
                    targetRpg * (1 - m_priv.info.currentFrame.faceAdjustConfidence);
                targetBpg = (1 / m_skinCoreOut.skinCoreOut.final_face_wb_b_gain) * m_priv.info.currentFrame.faceAdjustConfidence +
                    targetBpg * (1 - m_priv.info.currentFrame.faceAdjustConfidence);
            }

            float outRpg = 0;
            float outBpg = 0;
            float outCtemp = 0;
            CAM_ALGO_LOG_VERBOSE("cs algo Speed enableControl %d, speedControl %f, stableThr %f", m_pTuning->baseParam.cs_speedControl.enableControl,
                m_pTuning->baseParam.cs_speedControl.speedControl, m_pTuning->baseParam.cs_speedControl.stableThr);

            if(m_pTuning->baseParam.cs_speedControl.enableControl)
            {
                float nowpConvInitRpg[2] = {m_priv.info.currentFrame.fallbackInfo.cnvgEst.RpG, m_priv.info.currentFrame.fallbackInfo.cnvgEst.RpG};
                m_convMap[ConvE::NOWP_RPG]->ResetConvValue(nowpConvInitRpg, 2);
                m_convMap[ConvE::NOWP_RPG]->ExecConv(targetRpg, &outRpg);

                float nowpConvInitBpg[2] = {m_priv.info.currentFrame.fallbackInfo.cnvgEst.BpG, m_priv.info.currentFrame.fallbackInfo.cnvgEst.BpG};
                m_convMap[ConvE::NOWP_BPG]->ResetConvValue(nowpConvInitBpg, 2);
                m_convMap[ConvE::NOWP_BPG]->ExecConv(targetBpg, &outBpg);

                float nowpConvInitCtemp[2] = {(float)m_priv.info.currentFrame.fallbackInfo.ctemp, (float)m_priv.info.currentFrame.fallbackInfo.ctemp};
                m_convMap[ConvE::NOWP_CTEMP]->ResetConvValue(nowpConvInitCtemp, 2);
                m_convMap[ConvE::NOWP_CTEMP]->ExecConv((float)targetCtemp, &outCtemp);
            }
            else
            {
                outRpg = targetRpg;
                outBpg = targetBpg;
                outCtemp = targetCtemp;
            }

            SOpAwb_DayLightParam *pDayLightMixWeightParam = &m_pTuning->modeParam.pAwbTuningParam->opAwb_TblDayLightMixParam;
            int moon_trigerFlag = CalcMoonTrigerflag();
            if((m_pTuning->baseParam.moonParam.enable) && ((m_pTuning->baseParam.moonParam.moonModeID) == m_priv.info.awbMode) && (moon_trigerFlag == 1))
            {
                outRpg = m_pTuning->baseParam.moonParam.moonResultRpg;
                outBpg = m_pTuning->baseParam.moonParam.moonResultBpg;
                outCtemp = CommonCalcCorrelateColorTemperature(outRpg, outBpg, &m_priv.info.tuningParam.WBGainParam.mapInfo, m_pTuning->baseParam.pCct->ctempTable);
                CAM_ALGO_LOG_VERBOSE("moon result = %f %f %f", outRpg, outBpg, outCtemp);
            }
            else if(pDayLightMixWeightParam->opAwbDLMixParam.dayLightMixEnable)
            {
                float mixWeight = CalcDayLightWeight();

                float gslGain[eOpAwb_BoundaryMapXYCnt] = { 1.0, 1.0 };
                if(m_priv.info.gslInfo.duvEnable){
                    //float gslGainV2[eOpAwb_BoundaryMapXYCnt] = { 1.0, 1.0 };
                    CalcGainScalingGainMapV2(gslGain);
                }else{
                    CalcGainScalingGainMap(pDayLightMixWeightParam->opAwbDLMixParam.lightRpg, pDayLightMixWeightParam->opAwbDLMixParam.lightBpg, gslGain);
                }

                float mixDayLightRpg = (1 - mixWeight) * outRpg + mixWeight * (pDayLightMixWeightParam->opAwbDLMixParam.lightRpg / (gslGain[0]+EPS));
                float mixDayLightBpg = (1 - mixWeight) * outBpg + mixWeight * (pDayLightMixWeightParam->opAwbDLMixParam.lightBpg / (gslGain[0]+EPS));

                m_priv.info.currentFrame.dayLightMixWeight = mixWeight;

                CAM_ALGO_LOG_VERBOSE("mixWeight %f lightRpg %f lightBpg %f, pRpG %f, pBpG %f\n",mixWeight, pDayLightMixWeightParam->opAwbDLMixParam.lightRpg,
                    pDayLightMixWeightParam->opAwbDLMixParam.lightBpg, outRpg, outBpg);

                outRpg = mixDayLightRpg;
                outBpg = mixDayLightBpg;
                outCtemp = CommonCalcCorrelateColorTemperature(mixDayLightRpg, mixDayLightBpg, &m_priv.info.tuningParam.WBGainParam.mapInfo, m_pTuning->baseParam.pCct->ctempTable);
            }

            CAM_ALGO_LOG_VERBOSE("cs algo targetRpg, targetBpg = (%f,%f), outRpg, outBpg, outCtemp =  (%f,%f), %f, currentFrame rgbg = (%f,%f)\n",
                targetRpg,targetBpg,outRpg,outBpg,outCtemp, m_priv.info.currentFrame.fallbackInfo.cnvgEst.RpG, m_priv.info.currentFrame.fallbackInfo.cnvgEst.BpG);

            m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.RGain = 1/(outRpg + EPS);
            m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.BGain = 1/(outBpg + EPS);

            m_priv.info.currentFrame.Mix_csalgo.RpG = 0.0;//1.0/(m_priv.info.currentFrame.cnvgWBGain.RGain+EPS);
            m_priv.info.currentFrame.Mix_csalgo.BpG = 0.0;//1.0/(m_priv.info.currentFrame.cnvgWBGain.BGain+EPS);

            m_priv.info.currentFrame.fallbackInfo.outputCtemp = (CTEMP)outCtemp;
            CAM_ALGO_LOG_VERBOSE("cs algo rgbg =(%f,%f), mixed rgbg = (%f,%f),outputCtemp:%f\n", csAlgoRpg, csAlgoBpg, outRpg, outBpg, (CTEMP)outCtemp);
        }
        else
        {
            m_priv.info.currentFrame.Mix_csalgo.RpG = 0.0;
            m_priv.info.currentFrame.Mix_csalgo.BpG = 0.0;
        }

        if(m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.RGain > 5.0 || m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.BGain > 5.0)
        {
           //fatal error,let screen to be green
           m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.RGain = 1.0;
           m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.BGain = 1.0;
        }
    }
    else
    {//Calculate WBGain
        CAM_ALGO_LOG_VERBOSE("use currentFrame intoMapCount: %d, Stats RpG: %5.6f, BpG: %5.6f, Wei: %5.6f", intoMapCount, integral.RpG, integral.BpG, integralWeight);
        totalTmp.RpG = (integral.RpG / (integralWeight+EPS));
        totalTmp.BpG = (integral.BpG / (integralWeight+EPS));
        m_priv.info.currentFrame.AGW_gray.RpG = totalTmp.RpG;
        m_priv.info.currentFrame.AGW_gray.BpG = totalTmp.BpG;
        CAM_ALGO_LOG_VERBOSE("AWB_stats:AGW_gray=(%f,%f)\n", totalTmp.RpG, totalTmp.BpG);

        m_priv.info.currentFrame.agwNoMap.RpG = integralNoMap.RpG / (integralWeightNoMap + EPS);
        m_priv.info.currentFrame.agwNoMap.BpG = integralNoMap.BpG / (integralWeightNoMap + EPS);
        CAM_ALGO_LOG_VERBOSE("AWB_stats:AGW_Without MAP gray=(%f,%f)\n", m_priv.info.currentFrame.agwNoMap.RpG,
            m_priv.info.currentFrame.agwNoMap.BpG);

        m_priv.info.currentFrame.fallbackInfo.integral.RpG = totalTmp.RpG;
        m_priv.info.currentFrame.fallbackInfo.integral.BpG = totalTmp.BpG;

        m_priv.info.currentFrame.intoMapCount = intoMapCount;
        CalcWB(totalTmp.RpG, totalTmp.BpG , camId);

        m_priv.info.currentFrame.integralWeight = integralWeight;
    }
    CAM_ALGO_LOG_VERBOSE("Stats RpG: %5.6f, BpG: %5.6f, Wei: %5.6f, Calced CTemp: %d, BV: %5.6f", integral.RpG, integral.BpG, integralWeight, m_priv.info.currentFrame.fallbackInfo.ctemp, m_priv.info.currentFrame.fallbackInfo.bv);
    CAM_ALGO_LOG_VERBOSE("RGain:%5.6f, GGain:%5.6f, BGain:%5.6f", m_priv.info.currentFrame.fallbackInfo.WBGain.RGain, m_priv.info.currentFrame.fallbackInfo.WBGain.GGain, m_priv.info.currentFrame.fallbackInfo.WBGain.BGain);
    CAM_ALGO_LOG_VERBOSE("CnvgRGain:%5.6f, CnvgGGain:%5.6f, CnvgBGain:%5.6f", m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.RGain, m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.GGain, m_priv.info.currentFrame.fallbackInfo.cnvgWBGain.BGain);
    return eOp_StatusOK;
}
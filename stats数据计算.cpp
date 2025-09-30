#define APS_NODE "QTI Debug Metadata"

typedef struct {
    unsigned int R;
    unsigned int G;
    unsigned int B;
    unsigned int Y;
} LogBlockStats;

typedef struct {
    unsigned short R;
    unsigned short G;
    unsigned short B;
    unsigned short Y;
} LogBlockStatsMTK;

typedef struct {
    unsigned int upperR;
    unsigned int upperG;
    unsigned int upperB;

    unsigned int lowerR;
    unsigned int lowerG;
    unsigned int lowerB;
} SOpStatsScreenThr;
void AWBExifParser::getProcessLog() {

    if (exif_.faceInfo.pAwbExifFaceInfo == nullptr) {
        CHRONOS_ERROR << "getProcessLog: pAwbExifFaceInfo is null";
        return;
    }
    int block_row = exif_.faceInfo.pAwbExifFaceInfo->stats_info_row;
    int block_col = exif_.faceInfo.pAwbExifFaceInfo->stats_info_col;
    int numOfBlocks = block_row * block_col;

    if (exif_.statsData.addr == nullptr || exif_.statsData.size == 0) {
        return;
    }

	// json中stats数据
    QByteArray stats_data(exif_.statsData.addr, exif_.statsData.size);
    removeAPSNode(stats_data);

    if (!exif_.pLogStatsWeightData) {
        return;
    }

    if (exif_.pLogStatsWeightData->platform_type == OP_AWB_PLATFORM_TYPE_MTK) {
        log_block_stats_mtk_.reset(new LogBlockStatsMTK[numOfBlocks]);
    } else {
        log_block_stats_qc_.reset(new LogBlockStats[numOfBlocks]);
    }

    char* tmp = stats_data.data();
    double rpg, bpg;
    double rpg_before, bpg_before;
    double pre_gain_rpg = 1.0;
    double pre_gain_bpg = 1.0;
    double rpg_otp, bpg_otp;
    int idx = 0;
    unsigned int YLevel;
    float correctCoefRpG, correctCoefBpG;

    if (exif_.pLogUnitToUnitData) {
        correctCoefRpG = exif_.pLogUnitToUnitData->correctCoefRpG;
        correctCoefBpG = exif_.pLogUnitToUnitData->correctCoefBpG;
    } else {
        correctCoefRpG = 1.0;
        correctCoefBpG = 1.0;
    }

    SOpStatsScreenThr statsScreenThr;
    OpAwb_GetLevelGateThreshold(&statsScreenThr);
    int skinBlockCount = 0;
    for (int i = 0; i < block_row; i++) {
        for (int j = 0; j < block_col; j++) {
            idx = i * block_col + j;
            if (exif_.pLogStatsWeightData->platform_type == OP_AWB_PLATFORM_TYPE_MTK) {
                memcpy((char*)(&log_block_stats_mtk_[idx]), tmp, sizeof(LogBlockStatsMTK));
                tmp += sizeof(LogBlockStatsMTK);
                unsigned short R = log_block_stats_mtk_[idx].R;
                unsigned short B = log_block_stats_mtk_[idx].B;
                unsigned short G = log_block_stats_mtk_[idx].G;
                unsigned short Y = log_block_stats_mtk_[idx].Y;
                if (((R < statsScreenThr.lowerR) || (statsScreenThr.upperR < R)) ||
                    ((G < statsScreenThr.lowerG) || (statsScreenThr.upperG < G)) ||
                    ((B < statsScreenThr.lowerB) || (statsScreenThr.upperB < B))) {
                    continue;
                } else {
                    rpg = (double)R / G;
                    bpg = (double)B / G;
                    YLevel = Y;
                    rpg = rpg * (1.0 / pre_gain_rpg);
                    bpg = bpg * (1.0 / pre_gain_bpg);
                    rpg_otp = rpg * correctCoefRpG;
                    bpg_otp = bpg * correctCoefBpG;
                }
            } else {
                memcpy((char*)(&log_block_stats_qc_[idx]), tmp, sizeof(LogBlockStats));
                tmp += sizeof(LogBlockStats);
                unsigned int R = log_block_stats_qc_[idx].R;
                unsigned int B = log_block_stats_qc_[idx].B;
                unsigned int G = log_block_stats_qc_[idx].G;
                unsigned int Y = log_block_stats_qc_[idx].Y;
                if (((R < statsScreenThr.lowerR) || (statsScreenThr.upperR < R)) ||
                    ((G < statsScreenThr.lowerG) || (statsScreenThr.upperG < G)) ||
                    ((B < statsScreenThr.lowerB) || (statsScreenThr.upperB < B))) {
                    continue;
                } else {
                    rpg = (double)R / G;
                    bpg = (double)B / G;
                    YLevel = Y;
                    rpg_otp = rpg * correctCoefRpG;
                    bpg_otp = bpg * correctCoefBpG;
                }
            }
            block_indexs_.append(QPoint(i, j));
            block_before_otp_points_.append(QPointF(rpg, bpg));
            block_after_otp_points_.append(QPointF(rpg_otp, bpg_otp));
            is_skinblock_.append(exif_.faceInfo.pAwbExifFaceInfo->isSkinBlock[skinBlockCount++] == 1);
            block_ylevel_.append(YLevel);
        }

    }
}

void AWBExifParser::setStatsScreenParam(SOpStatsScreen_TuningParam* statsScreenTuningParam) {
    statsScreenTuningParam_ = statsScreenTuningParam;
}

double AWBExifParser::getCurrentFrame_bv() {
    if (exif_.pLogMetaData) {
        return exif_.pLogMetaData->currentFrame_bv / 1024.0;
    } else {
        return -1;
    }
}

void AWBExifParser::OpAwb_GetLevelGateThreshold(SOpStatsScreenThr* statsScreenThr) {
    unsigned int block_height = exif_.pLogMetaData->blockHeight;
    unsigned int block_width = exif_.pLogMetaData->blockWidth;
    unsigned int bitDepth = exif_.pLogStatsWeightData->bitDepth;
    float dolCompen = 1.0;
    short qcomAverageStatsEnable = 0;
    if (exif_.pAssistInfoLog) {
        dolCompen = (exif_.pAssistInfoLog->dolCompen == 0) ? 1.0 : exif_.pAssistInfoLog->dolCompen;
        qcomAverageStatsEnable = exif_.pAssistInfoLog->averageStatsEnable;
    }

    if (!statsScreenTuningParam_) {
        statsScreenThr->upperR = (250 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        statsScreenThr->upperG = (250 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        statsScreenThr->upperB = (250 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        statsScreenThr->lowerR = (1 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        statsScreenThr->lowerG = (1 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        statsScreenThr->lowerB = (1 << (bitDepth - 8)) * (block_height * block_width / 4) / dolCompen;
        CHRONOS_ERROR << "OpAwb_GetLevelGateThreshold: statsScreenTuningParam_ is null";
        return;
    }

    float bv = getCurrentFrame_bv();

    float tempUpperR =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->saturated_screen_BV_start_thd,
                                     statsScreenTuningParam_->saturated_screen_BV_end_thd,
                                     statsScreenTuningParam_->saturated_thr_R, 4);

    float tempUpperG =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->saturated_screen_BV_start_thd,
                                     statsScreenTuningParam_->saturated_screen_BV_end_thd,
                                     statsScreenTuningParam_->saturated_thr_G, 4);

    float tempUpperB =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->saturated_screen_BV_start_thd,
                                     statsScreenTuningParam_->saturated_screen_BV_end_thd,
                                     statsScreenTuningParam_->saturated_thr_B, 4);

    float tempLowerR =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->dark_screen_BV_start_thd,
                                     statsScreenTuningParam_->dark_screen_BV_end_thd,
                                     statsScreenTuningParam_->dark_thr_R, 4);

    float tempLowerG =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->dark_screen_BV_start_thd,
                                     statsScreenTuningParam_->dark_screen_BV_end_thd,
                                     statsScreenTuningParam_->dark_thr_G, 4);

    float tempLowerB =
            OpAwb_StatsScreenThrCalc(bv, statsScreenTuningParam_->dark_screen_BV_start_thd,
                                     statsScreenTuningParam_->dark_screen_BV_end_thd,
                                     statsScreenTuningParam_->dark_thr_B, 4);

    if (exif_.pLogStatsWeightData->platform_type == OP_AWB_PLATFORM_TYPE_MTK) {
        statsScreenThr->upperR = (unsigned int)(tempUpperR * (1 << (MTK_STATS_UPPER_BITDEPTH - 8)));
        statsScreenThr->upperG = (unsigned int)(tempUpperG * (1 << (MTK_STATS_UPPER_BITDEPTH - 8)));
        statsScreenThr->upperB = (unsigned int)(tempUpperB * (1 << (MTK_STATS_UPPER_BITDEPTH - 8)));
        statsScreenThr->lowerR = (unsigned int)(tempLowerR * (1 << (bitDepth - 8)));
        statsScreenThr->lowerG = (unsigned int)(tempLowerG * (1 << (bitDepth - 8)));
        statsScreenThr->lowerB = (unsigned int)(tempLowerB * (1 << (bitDepth - 8)));
    } else {
        if (qcomAverageStatsEnable) {
            statsScreenThr->upperR = (unsigned int)(tempUpperR * (1 << (bitDepth - 8)));
            statsScreenThr->upperG = (unsigned int)(tempUpperG * (1 << (bitDepth - 8)));
            statsScreenThr->upperB = (unsigned int)(tempUpperB * (1 << (bitDepth - 8)));
            statsScreenThr->lowerR = (unsigned int)(tempLowerR * (1 << (bitDepth - 8)));
            statsScreenThr->lowerG = (unsigned int)(tempLowerG * (1 << (bitDepth - 8)));
            statsScreenThr->lowerB = (unsigned int)(tempLowerB * (1 << (bitDepth - 8)));
        } else {
            statsScreenThr->upperR = (unsigned int)(tempUpperR * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
            statsScreenThr->upperG = (unsigned int)(tempUpperG * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
            statsScreenThr->upperB = (unsigned int)(tempUpperB * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
            statsScreenThr->lowerR = (unsigned int)(tempLowerR * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
            statsScreenThr->lowerG = (unsigned int)(tempLowerG * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
            statsScreenThr->lowerB = (unsigned int)(tempLowerB * (1 << (bitDepth - 8)) * (block_height * block_width / 4));
        }
    }

    statsScreenThr->upperR = (statsScreenThr->upperR / dolCompen);
    statsScreenThr->upperG = (statsScreenThr->upperG / dolCompen);
    statsScreenThr->upperB = (statsScreenThr->upperB / dolCompen);
    statsScreenThr->lowerR = (statsScreenThr->lowerR / dolCompen);
    statsScreenThr->lowerG = (statsScreenThr->lowerG / dolCompen);
    statsScreenThr->lowerB = (statsScreenThr->lowerB / dolCompen);
}
float AWBExifParser::OpAwb_StatsScreenThrCalc(float trigger_value, float start_zone[],
                                              float end_zone[], float zone_value[],
                                              int trigger_cnt) {
    int i;
    float weight;

    for (i = trigger_cnt; i > 0; i--) {
        if (trigger_value >= start_zone[i] && trigger_value < end_zone[i]) {
            weight = zone_value[i];
            return weight;
        } else if (trigger_value >= end_zone[i - 1] && trigger_value < start_zone[i]) {
            // interpolation to avoid sudden jump
            float x1 = trigger_value - end_zone[i - 1];
            float x2 = start_zone[i] - trigger_value;
            weight = (float)((x1 * zone_value[i] + x2 * zone_value[i - 1]) / (x1 + x2));
            return weight;
        }
    }

    if (trigger_value >= start_zone[0] && trigger_value < end_zone[0]) {
        weight = zone_value[0];
        return weight;
    } else if (trigger_value < start_zone[0]) {
        return zone_value[0];
    } else if (trigger_value >= end_zone[trigger_cnt]) {
        return zone_value[trigger_cnt];
    }

    return -1;
}

#define APS_NODE "QTI Debug Metadata"
void AWBExifParser::removeAPSNode(QByteArray& log) {

    int slice_pos = log.indexOf(APS_NODE); // segment slice
    if (slice_pos >= 4) {
        log = log.remove(slice_pos - 4, 23);
        removeAPSNode(log);
    }
}

// xml工程中数据位置
void ViewerTuningCommonParameters::OpAwb_GetStatsScreenTuningParam(
        SOpStatsScreen_TuningParam* statsScreenTuningParam) {
    if (nullptr == statsScreenTuningParam) {
        return;
    }

    auto statsScreenParamNode = root_->findParameter("awb_scenario/AwbTuningParameter/statsScreenParam");
    for (int i = 0; i < 5; i++) {
        statsScreenTuningParam->saturated_screen_BV_start_thd[i] =
                statsScreenParamNode->findParameterValue(QString("saturated_screen_BV_start_thd/%1").arg(i)).toFloat();
        statsScreenTuningParam->saturated_screen_BV_end_thd[i] =
                statsScreenParamNode->findParameterValue(QString("saturated_screen_BV_end_thd/%1").arg(i)).toFloat();
        statsScreenTuningParam->dark_screen_BV_start_thd[i] =
                statsScreenParamNode->findParameterValue(QString("dark_screen_BV_start_thd/%1").arg(i)).toFloat();
        statsScreenTuningParam->dark_screen_BV_end_thd[i] =
                statsScreenParamNode->findParameterValue(QString("dark_screen_BV_end_thd/%1").arg(i)).toFloat();
        statsScreenTuningParam->saturated_thr_R[i] =
                statsScreenParamNode->findParameterValue(QString("saturated_thr_R/%1").arg(i)).toFloat();
        statsScreenTuningParam->saturated_thr_G[i] =
                statsScreenParamNode->findParameterValue(QString("saturated_thr_G/%1").arg(i)).toFloat();
        statsScreenTuningParam->saturated_thr_B[i] =
                statsScreenParamNode->findParameterValue(QString("saturated_thr_B/%1").arg(i)).toFloat();
        statsScreenTuningParam->dark_thr_R[i] =
                statsScreenParamNode->findParameterValue(QString("dark_thr_R/%1").arg(i)).toFloat();
        statsScreenTuningParam->dark_thr_G[i] =
                statsScreenParamNode->findParameterValue(QString("dark_thr_G/%1").arg(i)).toFloat();
        statsScreenTuningParam->dark_thr_B[i] =
                statsScreenParamNode->findParameterValue(QString("dark_thr_B/%1").arg(i)).toFloat();
    }
}

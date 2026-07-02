detectAlgo //人脸检测模型 ，可置为3种类型：
faceDetCop_HISI		// BGR输入，CPU预处理的人脸检测
faceDetCop_IveBGRInput_HISI	// BGR输入，IVE预处理的人脸检测
faceDetCop_IveYuvInput_HISI	// YUV输入，IVE预处理的人脸检测，选择YUV输入时应确认输入有效

alignDetAlgo //人脸优选定点模型，仅可配置为1种类型
AlignDet_HISI

alignAlgo //人脸定点模型，可配置为2种类型
Align_HISI                //21点定点，对应工程V2
Classification_HISI       //5点定点，对应工程V3

verifyAlgo //人脸特征提取模型，  仅可配置为1种类型
Classification_HISI

qualityAlgo //人脸质量模型， 可配置为2种类型
Classification_HISI	                // BGR输入，CPU预处理的质量网络
ClassificationYuvInput_HISI	// YUV输入，IVE预处理的质量网络，选择YUV输入时应确认输入有效

attributeAlgo //人脸属性模型， 仅可配置为1种类型
Classification_HISI










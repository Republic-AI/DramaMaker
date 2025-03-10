
本协议使用google protocolbuffer为通信原型，请参考protocolbuffer官方文档



协议文件编写格式约束如下：
	1. 使用proto3规范
	2. 协议需要引入报名，统一是使用com.inmont.protocol;
	3. 协议如果是命令文件，需要指定命令号和节点，具体描述参考QueryGoodsCommand.proto文件;
	4. 在设计命令协议里面必须要带入requestId,保持请求的唯一性.


1. 重新生成所有的命令使用build_all.cmd命令，命令不带任何参数
2. 生成指定协议使用rebuild_cmd.cmd命令，命令使用如下:
	build_cmd.cmd "protofile"




pip install protobuf==3.9.1
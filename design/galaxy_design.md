# Galaxy集群操作系统总体设计


修改记录:
<table>
<tr align='center'><td>时间</td><td>修改人</td><td>内容</td></tr>
<tr><td>2015/04/30</td><td>颜世光</td><td>原文</td></tr>
</table>

## 背景
承载搜索引擎业务的大型分布式集群包含上万台机器，机器上运行着各式各样的应用，应用部署时要考虑资源冗余，所以大量机器资源是闲置的，如果将多个应用部署在一起共享冗余资源，应用间又会相互干扰，严重影响了服务的稳定性。另外，当应用系统规模达到千台，部署就成为一个耗时且繁复的任务。所以，需要有一个基础系统处理应用的部署和隔离。

## 设计目标

### 功能目标
1. 机器管理  
	a. 机器初始化  
	b. 硬件参数收集  
	c. 硬件故障检测与自动维修
2. 应用调度  
	a. 服务自动化部署  
	b. 服务失败自动恢复  
    c. 灰度发布  
	d. 日志收集与监控  
3. Mapreduce编程框架  
	支持已有业务大量的mapreduce程序迁移、运行
4. 集群数据存储  
	提供数据中心级的统一存储

### 扩展性目标
第一版单集群支持5000台机器，在主要功能完善后进行重构，支持1万+机器的数据中心。

## 系统设计
系统使用master-slave结构，主要由总控节点Master和执行节点Agent构成，Master负责核心数据的存储与任务的分配，Agent负责任务的执行。并提供统一的客户端galaxy_client完成用户操作。

系统的外围是监控与日志收集子系统，负责将系统内任务的状态与数据进行收集和展示。

系统底层依赖分布式文件系统持久化数据。

### Master模块设计
Master职责：  
1. Agent状态管理  
2. 资源管理  
3. 任务管理  
4. 任务调度

Master接收Agent的心跳信息判断Agent是否存活，Master将当前存活的Agent加入可用机器列表，并通过定期Query获取Agent上的资源配置与运行的任务信息。

Master将Query到的资源信息放入统一的资源池管理，按照利用率最大化的目标分配给有资源需求的作业。

Master响应Client的作业提交，持久化作业信息，提供作业信息的查询，并根据用户的配额决定作业是否可以被调度。

Master根据作业的资源需求将作业分配到符合要求的Agent上执行。

Master使用主从互备的方式保证高可用。

### Agent模块设计
Agent职责：  
1. 运行环境初始化与隔离  
2. 任务运行期存活性监控  
3. 任务资源控制  
4. 任务资源使用统计

Agent将所有任务运行在容器里，在接收到Master分配的任务时，预先为任务运行初始化环境，为每个任务创建一个单独的容器，保证任务运行环境的隔离。

Agent将所有任务作为子进程管理，并持续监控任务的运行状态，任务退出后，Agent获取任务的返回码判断任务是否执行完成。对于出错退出的任务，Agent会按重试次数配置进行有限次重试，超过重试次数的任务标记失败，等待Master通过query获取任务的状态。

Agent通过CGroup限制任务的资源使用，提供Quota和limit两种限制，Quota是可以保证的资源使用，limit是最大可使用的资源，如CPU的quota是10，limit是20，即可以保证任务有10个单位的CPU可以使用，在机器上CPU资源空闲时，任务可以使用到20个单位的CPU。如果一个任务在运行期间使用的资源超过quota，在系统资源不足时，Agent负责回收这部分资源，CPU等可伸缩的资源会通过参数调整降低，但内存等不可伸缩的资源，将会导致直接kill掉对应任务，所以对于无法承受超限kill的任务，可以将limit配置的和quota一致。

## 各子系统设计
### 任务管理系统
Galaxy将用户任务按作业(Job)组织，一个作业就是一系列共享一个执行体的任务，它们一般是一个服务的多个分片，galaxy负责维护一个作业内的任务个数的稳定，但不负责用户的分片逻辑。
Master负责管理所有任务信息，接收用户任务的提交，并将任务信息持久化，并根据用户的需求，将任务调度到Agent上执行。

### WebUI
WebUI是galaxy系统的用户界面，用户通过Web提交、编辑、删除任务，通过Web查看任务状态、添加监控与起停日志收集任务。

管理员通过web进行用户和集群的管理。

### 日志收集系统
日志收集需求与作业(Job)绑定，用户提交的作业请求中包含要收集哪些日志，存储在哪里等信息。
作业的任务在被调度执行时，Agent会针对每个Task运行一个日志收集进程，负责将日志收集并传输到指定的位置。

### 监控系统
监控需求与作业绑定，用户提交的作业请求中包含监控项与报警方式。作业的任务在被调度执行时，Agent会针对每个Task运行一个监控程序，执行各项监控。监控的添加与删除通过更新作业信息实现。

### 程序包管理
程序包管理包含统一的分布式存储和Agent本地的缓存两部分。
统一存储由DFS上线，Agent本地缓存提供本地Agent缓存的同时，可以提供P2P传输服务。

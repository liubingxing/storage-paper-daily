---
date: 2026-03-26
categories:
  - 论文精读
  - FAST'23
tags:
  - LSM-tree
  - database
  - logging
---

# 【论文精读】Removing Double-Logging with Passive Data Persistence in LSM-tree Based Relational Databases

> **会议**: FAST'23 | **日期**: 2026-03-26
> **标签**: LSM-tree, database, logging

# Removing Double-Logging with Passive Data Persistence in LSM-tree Based Relational Databases

---

## 论文基本信息

- **论文标题**: Removing Double-Logging with Passive Data Persistence in LSM-tree Based Relational Databases  
- **发表会议**: FAST (File and Storage Technologies), 2023  
- **研究方向**: 数据库存储系统，特别是基于 LSM-tree 的关系型数据库的日志优化  

这篇论文聚焦于 LSM-tree（Log-Structured Merge Tree）存储引擎中日志记录（logging）机制的优化，提出了一种称为“被动数据持久化”（Passive Data Persistence, PDP）的新方法，以消除传统 LSM-tree 存储引擎中的双日志（double-logging）问题。

---

## 研究背景与动机

### 需要解决的问题
在基于 LSM-tree 的关系型数据库（例如 RocksDB、LevelDB 等）中，写操作通常会依次经历以下流程：
1. 写入到内存中的 MemTable；
2. 将写操作的日志记录到 Write-Ahead Log (WAL) 中，以实现崩溃后恢复的能力；
3. 定期将 MemTable 刷新到 SSTable（磁盘上的文件）。

在这一流程中，WAL 的存在是为了保证数据的持久化和崩溃恢复能力。然而，这种设计引入了“**双日志问题（double-logging）**”：
- 数据同时写入 WAL 和 MemTable，导致了 **冗余写放大（write amplification）**，增加了存储系统的 I/O 开销。
- WAL 的写入是顺序的，而 MemTable 是随机访问的，因此也会引起 **性能不一致** 的问题。
- 双日志机制使得事务提交的延迟增加，影响了数据库的吞吐量。

### 重要性分析
- **性能瓶颈**: LSM-tree 数据库通常应用于高性能场景（如在线事务处理 OLTP 和分析型工作负载 OLAP）。双日志问题限制了数据库的吞吐量和写入性能，严重影响了系统的可扩展性。
- **硬件性能限制**: 即使使用现代的高性能存储设备（如 NVMe SSD），双日志问题仍然会导致 I/O 资源浪费，未充分利用硬件性能。
- **崩溃一致性**: 尽管 WAL 解决了崩溃时数据恢复的问题，但它带来的存储和性能开销使得更高效的解决方案成为必要。

### 现有方案与不足
1. **传统 WAL (Write-Ahead Logging)**  
   - **机制**: 每次事务写入都会被追加到 WAL 文件中，并在 MemTable 中更新数据结构。
   - **问题**: 双写操作带来了冗余的写放大，影响了性能。

2. **Group Commit**  
   - **机制**: 将多个事务的日志批量写入 WAL，从而减少写放大问题。
   - **问题**: 引入了更高的提交延迟，且无法完全消除双写问题。

3. **No-WAL 模式**  
   - **机制**: 跳过 WAL，直接将数据写入 MemTable，并通过定期快照恢复。
   - **问题**: 崩溃恢复时间过长，数据可能丢失。

### 核心 insight
论文的核心 insight 是：**利用 LSM-tree 的固有特性，设计一种被动数据持久化（Passive Data Persistence, PDP）机制，消除传统 WAL 的双写问题，同时确保崩溃一致性和高性能。**  
具体来说，通过将数据直接写入 MemTable，并利用 LSM-tree 的异步持久化机制（即 MemTable 到 SSTable 的刷盘操作）来替代 WAL 的作用，在保证数据一致性的同时，显著降低写放大和延迟。

---

## 架构设计图

以下是论文提出的被动数据持久化（PDP）架构的核心设计图：

```mermaid
flowchart TB
  subgraph 内存层
    A1[WAL (传统写前日志)]:::cylinder -->|写入WAL| A2[MemTable]:::rect
    A2 -->|刷新| A3[SSTable]:::cylinder
  end

  subgraph PDP架构
    B1[事务请求]:::circle -->|直接写入| B2[MemTable]:::rect
    B2 -->|异步刷盘| B3[SSTable]:::cylinder
    B3 -->|崩溃恢复| B5[恢复引擎]:::rect
    B2 -->|持久化元数据| B4[元数据存储]:::rect
  end

  style A1 fill:#f9f,stroke:#333,stroke-width:4px
  style B1 fill:#9f9,stroke:#333,stroke-width:4px

  %% 图例
  classDef rect fill:#bbf,stroke:#333,stroke-width:2px;
  classDef cylinder fill:#ffe,stroke:#333,stroke-width:2px;
  classDef circle fill:#f66,stroke:#333,stroke-width:2px;
```

### 图示说明
- **传统方案**（左侧）：写操作需要同时写入 WAL 和 MemTable，导致写放大。
- **PDP 方案**（右侧）：直接写入 MemTable，依赖异步刷盘到 SSTable 提供持久化保证，同时将元数据记录到轻量级的元数据存储中用于恢复。

---

## 核心设计与技术贡献

### 整体架构
论文提出了一种去除传统双日志的新架构，由以下核心组件构成：
1. **MemTable**: 内存中的数据缓冲区，负责接收写入操作。
2. **SSTable**: 磁盘上的持久化文件，存储经过排序和合并的数据。
3. **元数据存储**: 存储与事务相关的元数据（例如事务 ID 和写入范围），用于崩溃恢复。
4. **恢复引擎**: 在系统崩溃后，结合元数据和 SSTable 内容恢复一致性状态。

数据流和控制流：
- 写操作直接写入 MemTable。
- 定期将 MemTable 刷盘为 SSTable，提供数据的持久化保证。
- 元数据存储记录事务范围信息，用于崩溃时的恢复。

### 关键技术点

#### 1. 被动数据持久化（Passive Data Persistence, PDP）
- **子问题**: 如何在不使用 WAL 的情况下，保证崩溃后数据的一致性？
- **设计方案**:  
  - 依赖 LSM-tree 的天然持久化机制（MemTable 刷盘到 SSTable），确保数据最终会持久化到磁盘。
  - 通过引入元数据存储，仅保存事务的范围信息（如事务 ID、涉及的键范围），而无需记录完整的写入操作。
  - 崩溃时，恢复引擎通过元数据和 SSTable 内容检查一致性并回滚未完成的事务。
- **设计权衡**:  
  - **优点**: 消除了 WAL 写入，减少了写放大和存储开销。
  - **缺点**: 对恢复引擎的复杂性提出了更高要求。

#### 2. 元数据优化
- **子问题**: 如何高效存储和管理事务元数据？
- **设计方案**:  
  - 引入了轻量级的元数据存储，仅记录事务的键范围和状态（提交/未提交）。
  - 使用高效的数据结构（如 B+ 树或哈希表）存储元数据，提供快速查询支持。
- **设计权衡**:  
  - **优点**: 元数据存储占用空间小，查询速度快。
  - **缺点**: 元数据需要和数据刷盘操作精确协调，增加了系统复杂性。

#### 3. 崩溃恢复机制
- **子问题**: 如何在崩溃后快速恢复一致性？
- **设计方案**:  
  - 恢复引擎通过元数据存储确定未完成事务，并根据 SSTable 内容回滚未完成的写入。
  - 利用 LSM-tree 的多版本并发控制（MVCC）特性，避免对已提交数据的影响。
- **设计权衡**:  
  - **优点**: 崩溃恢复时间较短，且不依赖传统 WAL。
  - **缺点**: 恢复逻辑更复杂。

### 创新点总结
- **核心创新**: 利用 LSM-tree 的持久化特性和轻量级元数据存储，完全去除了传统的 WAL。
- **原因分析**: 传统方案中 WAL 是不可或缺的组件，而该论文通过重新设计恢复机制，证明了 WAL 的冗余性。

---

## 实验评估亮点

### 实验设置
- **基准测试**: YCSB（Yahoo Cloud Serving Benchmark）和 TPC-C。
- **比较基线**: RocksDB 和 MongoDB 的传统 WAL 方案。
- **硬件环境**: 标准 SSD 和 NVMe SSD。

### 实验结果
1. **吞吐量提升**: 相较于 RocksDB，写入吞吐量提高了约 30%-50%。  
2. **延迟降低**: 事务提交延迟降低了约 40%。  
3. **崩溃恢复时间**: 恢复时间与传统 WAL 相当，但存储开销显著减少。

### 实验结论
- 被动数据持久化有效减少了双写问题，显著提升了性能。
- 恢复机制的效率得到了验证，与传统方法相比无明显劣势。

---

## 与工业界的关联

### 工业界实践
- 类似的优化思路可以在存储引擎中推广，例如 RocksDB 和 LevelDB。
- 减少写放大和日志存储需求对云服务提供商（如 AWS S3, Google Cloud Storage）具有重要意义。

### 工程落地挑战
1. **崩溃恢复机制复杂度**: 如何确保元数据存储和数据刷盘的原子性？
2. **调优难度**: PDP 的参数调优需要结合具体工作负载特性，可能增加运维负担。

---

## 个人思考启发

### 值得学习的点
- 借助 LSM-tree 的特性，设计了一种优雅的解决方案，彻底消除了传统的双写问题。
- 提出了轻量级元数据存储的概念，为崩溃恢复提供支持。

### 潜在局限性
- 在高并发写入场景下，元数据存储可能成为瓶颈。
- 崩溃恢复机制的复杂性可能影响系统的可维护性。

### 启示
- 设计存储系统时，应充分挖掘底层数据结构的特性，以减少冗余开销。
- 崩溃恢复既是性能优化的重要方向，也是系统设计的一大挑战。

--- 

如果有任何细节需要补充或进一步展开，请指出！

# -*- coding: utf-8 -*-
"""
Seed Script - 写入假数据到系统
"""
import asyncio
import uuid
import random
import math
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.models.user import User
from app.models.rbac import Role
from app.models.industrial import ProductionLine, Device, Batch
from app.models.defect import DefectType, DefectSample, DefectResult
from app.models.timeseries import TimeseriesDataset, TimeseriesPoint, TimeseriesAnomaly, AnalysisReport
from app.models.system import Notification, AnalysisJob


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # --- 获取 admin 用户和组织 ---
        result = await db.execute(select(User).where(User.username == "admin"))
        admin = result.scalar_one_or_none()
        if not admin:
            print("ERROR: admin 用户不存在，请先启动后端服务创建默认数据")
            return
        admin_id = admin.id
        org_id = admin.organization_id
        print(f"Admin ID: {admin_id}")

        # ========== 1. 生产线 ==========
        lines_data = [
            ("SMT贴片产线A", "LINE-SMT-A", "SMT贴片生产线，负责PCB板贴片", "A栋1楼"),
            ("SMT贴片产线B", "LINE-SMT-B", "SMT贴片生产线（备用线）", "A栋2楼"),
            ("组装产线C", "LINE-ASM-C", "产品组装产线", "B栋1楼"),
            ("包装产线D", "LINE-PKG-D", "产品包装与质检产线", "B栋2楼"),
            ("注塑产线E", "LINE-INJ-E", "塑料注塑成型产线", "C栋1楼"),
        ]
        production_lines = []
        for name, code, desc, loc in lines_data:
            pl = ProductionLine(
                id=uuid.uuid4(), name=name, code=code, description=desc,
                location=loc, status="active", organization_id=org_id,
            )
            db.add(pl)
            production_lines.append(pl)
        await db.flush()
        print(f"已创建 {len(production_lines)} 条生产线")

        # ========== 2. 设备 ==========
        device_templates = [
            ("AOI光学检测仪", "AOI", "视觉检测", "AOI-5000", "基恩士", "深圳A栋"),
            ("SPI锡膏检测仪", "SPI", "锡膏检测", "SPI-3000", "科视达", "深圳A栋"),
            ("X-Ray检测机", "XRAY", "X射线检测", "XR-2000", "蔡司", "深圳A栋"),
            ("贴片机", "SMT", "贴片设备", "NXT-III", "富士", "深圳A栋"),
            ("回流焊炉", "REFLOW", "焊接设备", "RF-850", "日东", "深圳A栋"),
            ("波峰焊机", "WAVE", "焊接设备", "WS-450", "ERSA", "深圳B栋"),
            ("ICT在线测试仪", "ICT", "电气测试", "ICT-200", "德律", "深圳B栋"),
            ("功能测试机", "FCT", "功能测试", "FCT-100", "自研", "深圳B栋"),
            ("激光打标机", "LASER", "标记设备", "LM-50", "大族", "深圳C栋"),
            ("自动包装机", "PACK", "包装设备", "AP-300", "利乐", "深圳B栋"),
            ("温湿度传感器", "SENSOR", "环境监控", "TH-200", "西门子", "全厂区"),
            ("振动传感器", "VIBR", "设备监控", "VB-100", "SKF", "A栋B栋"),
        ]
        devices = []
        statuses = ["online", "online", "online", "online", "offline", "maintenance"]
        for i, (name, code_prefix, dtype, model, mfr, loc) in enumerate(device_templates):
            line = production_lines[i % len(production_lines)]
            dev = Device(
                id=uuid.uuid4(), name=name, code=f"DEV-{code_prefix}-{str(i+1).zfill(3)}",
                device_type=dtype, model=model, manufacturer=mfr,
                serial_number=f"SN{random.randint(100000, 999999)}",
                description=f"{name} - {model}", location=loc,
                status=random.choice(statuses),
                health_score=round(random.uniform(65, 100), 1),
                production_line_id=line.id,
                config={"interval": random.choice([5, 10, 30, 60])},
                last_maintenance_at=datetime.utcnow() - timedelta(days=random.randint(1, 90)),
            )
            db.add(dev)
            devices.append(dev)
        await db.flush()
        print(f"已创建 {len(devices)} 台设备")

        # ========== 3. 生产批次 ==========
        batches = []
        batch_statuses = ["completed", "completed", "completed", "in_progress", "in_progress", "pending"]
        product_types = ["PCB-A型主板", "PCB-B型控制板", "电源模块", "传感器模组", "通信模块"]
        for i in range(15):
            start = datetime.utcnow() - timedelta(days=random.randint(1, 60))
            bstatus = random.choice(batch_statuses)
            end = start + timedelta(hours=random.randint(4, 48)) if bstatus == "completed" else None
            b = Batch(
                id=uuid.uuid4(),
                batch_no=f"BAT-{start.strftime('%Y%m%d')}-{str(i+1).zfill(3)}",
                name=f"第{i+1}批次生产",
                product_type=random.choice(product_types),
                quantity=random.randint(100, 5000),
                status=bstatus,
                start_time=start, end_time=end,
                production_line_id=random.choice(production_lines).id,
            )
            db.add(b)
            batches.append(b)
        await db.flush()
        print(f"已创建 {len(batches)} 个生产批次")

        # ========== 4. 缺陷类型 ==========
        defect_types_data = [
            ("虚焊", "COLD_SOLDER", "焊接缺陷", "high", "焊点未完全熔合"),
            ("短路", "SHORT_CIRCUIT", "焊接缺陷", "critical", "焊点之间短路连接"),
            ("少锡", "LESS_SOLDER", "焊接缺陷", "medium", "焊锡量不足"),
            ("多锡", "EXCESS_SOLDER", "焊接缺陷", "low", "焊锡量过多"),
            ("偏移", "OFFSET", "贴片缺陷", "medium", "元器件贴装偏移"),
            ("缺件", "MISSING", "贴片缺陷", "critical", "元器件缺失"),
            ("极性反", "POLARITY", "贴片缺陷", "high", "极性方向错误"),
            ("裂纹", "CRACK", "基板缺陷", "high", "PCB板面裂纹"),
            ("划伤", "SCRATCH", "表面缺陷", "low", "产品表面划伤"),
            ("气泡", "BUBBLE", "注塑缺陷", "medium", "注塑件内部气泡"),
        ]
        defect_types = []
        for name, code, cat, sev, desc in defect_types_data:
            dt = DefectType(
                id=uuid.uuid4(), name=name, code=code, category=cat,
                severity=sev, description=desc, is_active=True,
                detection_params={"threshold": round(random.uniform(0.5, 0.9), 2)},
            )
            db.add(dt)
            defect_types.append(dt)
        await db.flush()
        print(f"已创建 {len(defect_types)} 种缺陷类型")

        # ========== 5. 缺陷样本 + 检测结果 ==========
        defect_samples = []
        for i in range(30):
            dev = random.choice(devices)
            bat = random.choice(batches)
            status = random.choice(["completed", "completed", "completed", "pending", "analyzing"])
            sample = DefectSample(
                id=uuid.uuid4(),
                sample_no=f"SAMPLE-{datetime.utcnow().strftime('%Y%m%d')}-{str(i+1).zfill(4)}",
                name=f"样本_{i+1}",
                sample_type=random.choice(["image", "image", "video"]),
                file_name=f"sample_{i+1}.jpg",
                file_size=random.randint(50000, 5000000),
                file_type="image/jpeg",
                image_width=random.choice([640, 1280, 1920, 2048]),
                image_height=random.choice([480, 720, 1080, 1536]),
                source=random.choice(["upload", "camera", "camera"]),
                device_id=dev.id, batch_id=bat.id,
                uploaded_by=admin_id,
                status=status,
            )
            db.add(sample)
            defect_samples.append(sample)

            # 为 completed 的样本添加检测结果
            if status == "completed":
                has_defect = random.random() < 0.4  # 40% 缺陷率
                dr = DefectResult(
                    id=uuid.uuid4(),
                    sample_id=sample.id,
                    defect_type_id=random.choice(defect_types).id if has_defect else None,
                    has_defect=has_defect,
                    confidence=round(random.uniform(0.75, 0.99), 4) if has_defect else round(random.uniform(0.01, 0.3), 4),
                    bbox={"x": random.randint(50, 300), "y": random.randint(50, 300),
                          "w": random.randint(20, 100), "h": random.randint(20, 100)} if has_defect else None,
                    model_name="YOLOv8-Defect",
                    model_version="v2.1.0",
                    analysis_details={
                        "inference_time_ms": round(random.uniform(15, 80), 1),
                        "preprocessing": "resize_640",
                    },
                )
                db.add(dr)
        await db.flush()
        print(f"已创建 {len(defect_samples)} 个缺陷样本及检测结果")

        # ========== 6. 时序数据集 + 数据点 + 异常 ==========
        ts_names = [
            ("设备温度监控", "temperature", "℃"),
            ("设备振动监控", "vibration", "mm/s"),
            ("电机电流监控", "current", "A"),
            ("压力传感器数据", "pressure", "MPa"),
        ]
        datasets = []
        now = datetime.utcnow()
        for idx, (ds_name, dt, unit) in enumerate(ts_names):
            dev = devices[idx % len(devices)]
            start_time = now - timedelta(hours=24)
            ds = TimeseriesDataset(
                id=uuid.uuid4(), name=f"{dev.name}-{ds_name}",
                description=f"{dev.name}的{ds_name}数据",
                source_type="simulate", device_id=dev.id,
                data_type=dt, sampling_rate=1.0,
                total_points=1440,  # 24h * 60min
                start_time=start_time, end_time=now,
                created_by=admin_id, status="active",
                columns_config={"unit": unit, "label": ds_name},
            )
            db.add(ds)
            datasets.append(ds)
            await db.flush()

            # 生成时序数据点 (每分钟一个点, 24小时 = 1440 点)
            base_values = {"temperature": 45.0, "vibration": 2.5, "current": 12.0, "pressure": 1.2}
            amp = {"temperature": 8.0, "vibration": 1.5, "current": 3.0, "pressure": 0.3}
            base_val = base_values[dt]
            amplitude = amp[dt]

            points = []
            anomaly_indices = set(random.sample(range(1440), 8))  # 8 个异常点
            for j in range(1440):
                t = start_time + timedelta(minutes=j)
                # 正弦波 + 噪声 + 趋势
                noise = random.gauss(0, amplitude * 0.1)
                trend = j * 0.001
                val = base_val + amplitude * math.sin(2 * math.pi * j / 480) + noise + trend
                if j in anomaly_indices:
                    val += random.choice([-1, 1]) * amplitude * random.uniform(2.5, 4.0)  # 异常偏移

                points.append(TimeseriesPoint(
                    id=uuid.uuid4(), dataset_id=ds.id,
                    timestamp=t, value=round(val, 3), quality=100 if j not in anomaly_indices else 50,
                ))

            db.add_all(points)

            # 记录异常
            for ai in anomaly_indices:
                t = start_time + timedelta(minutes=ai)
                anom = TimeseriesAnomaly(
                    id=uuid.uuid4(), dataset_id=ds.id,
                    anomaly_type=random.choice(["spike", "drift", "level_shift"]),
                    severity=random.choice(["low", "medium", "high"]),
                    timestamp=t, start_time=t,
                    end_time=t + timedelta(minutes=1),
                    value=round(points[ai].value, 3),
                    score=round(random.uniform(0.7, 0.99), 3),
                    threshold=round(base_val + amplitude * 2, 2),
                    description=f"检测到异常{dt}数值",
                    detection_method="zscore",
                    model_name="ZScoreDetector", model_version="v1.0",
                    status="detected",
                )
                db.add(anom)

        await db.flush()
        print(f"已创建 {len(datasets)} 个时序数据集, 共 {len(datasets)*1440} 个数据点, {len(datasets)*8} 个异常记录")

        # ========== 7. 分析报告 ==========
        for i, ds in enumerate(datasets):
            report = AnalysisReport(
                id=uuid.uuid4(),
                title=f"{ds.name} - 异常分析报告",
                report_type="timeseries",
                description=f"对{ds.name}进行24小时异常检测分析",
                content_json={
                    "total_points": 1440,
                    "anomaly_count": 8,
                    "anomaly_rate": "0.56%",
                    "methods": ["Z-Score", "移动平均"],
                    "conclusion": "检测到8处异常，建议关注设备运行状态",
                },
                content_markdown=f"# {ds.name} 分析报告\n\n## 概述\n数据点: 1440, 异常: 8\n\n## 结论\n设备运行整体正常，局部存在异常波动。",
                dataset_id=ds.id,
                created_by=admin_id,
                status="completed",
            )
            db.add(report)
        await db.flush()
        print(f"已创建 {len(datasets)} 份分析报告")

        # ========== 8. 分析任务 ==========
        job_statuses = ["completed", "completed", "completed", "running", "pending", "failed"]
        for i in range(8):
            ds = random.choice(datasets)
            jstatus = random.choice(job_statuses)
            job = AnalysisJob(
                id=uuid.uuid4(),
                name=f"分析任务-{i+1}",
                job_type=random.choice(["anomaly_detection", "trend_analysis", "defect_detection"]),
                description=f"自动分析任务 #{i+1}",
                config={"method": "zscore", "window": 60},
                status=jstatus,
                progress=100.0 if jstatus == "completed" else random.uniform(0, 80),
                result={"anomalies": random.randint(0, 10)} if jstatus == "completed" else None,
                error_message="内存不足，任务中止" if jstatus == "failed" else None,
                dataset_id=ds.id,
                started_at=datetime.utcnow() - timedelta(hours=random.randint(1, 48)),
                completed_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 120)) if jstatus == "completed" else None,
                created_by=admin_id,
            )
            db.add(job)
        await db.flush()
        print("已创建 8 个分析任务")

        # ========== 9. 通知 ==========
        notif_data = [
            ("设备离线告警", "设备 AOI光学检测仪 已离线超过10分钟，请及时检查", "warning"),
            ("异常检测完成", "设备温度监控数据异常检测完成，发现8处异常", "info"),
            ("批次质检完成", "BAT批次质检完成，合格率96.5%", "success"),
            ("系统维护通知", "系统将于今晚22:00进行例行维护，预计30分钟", "info"),
            ("新缺陷样本上传", "新增15个缺陷样本等待检测", "info"),
            ("设备健康度告警", "X-Ray检测机健康度降至72%，建议安排维保", "warning"),
            ("分析任务失败", "分析任务#5执行失败：内存不足", "error"),
            ("月度报告已生成", "2026年3月工业质检月度报告已自动生成", "success"),
        ]
        for title, content, ntype in notif_data:
            n = Notification(
                id=uuid.uuid4(), title=title, content=content,
                notification_type=ntype, user_id=admin_id,
                is_read=random.choice([True, False, False]),
            )
            db.add(n)
        await db.flush()
        print(f"已创建 {len(notif_data)} 条通知")

        # ========== 提交 ==========
        await db.commit()
        print("\n✅ 所有假数据写入完成!")
        print(f"   生产线: {len(production_lines)}")
        print(f"   设备: {len(devices)}")
        print(f"   批次: {len(batches)}")
        print(f"   缺陷类型: {len(defect_types)}")
        print(f"   缺陷样本: {len(defect_samples)}")
        print(f"   时序数据集: {len(datasets)} ({len(datasets)*1440} 个数据点)")
        print(f"   分析报告: {len(datasets)}")
        print(f"   分析任务: 8")
        print(f"   通知: {len(notif_data)}")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())

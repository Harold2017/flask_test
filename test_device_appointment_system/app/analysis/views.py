from . import analysis
from ..models import User, Device, user_device, DeviceUsageLog, GloveBoxLog
from .. import db
from flask import render_template, flash
from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import desc
from flask_login import login_required, current_user
from pyecharts import Pie, Line, Overlap, Gauge, Bar
from .forms import DeviceForm


tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')


def days_hours_minutes(td):
    return td.days, td.seconds//3600, (td.seconds//60)%60


@analysis.route('/', methods=['GET', 'POST'])
@login_required
def main():
    devices = Device.query.filter(~Device.name.op('regexp')('test.*')).all()
    cnt = 0
    for d in devices:
        if d.device_inuse is True:
            cnt += 1
    percentage = round(cnt / len(devices) * 100, 2)
    gauge = usage_gauge(percentage, is_legend_show=False)
    bar = None

    form = DeviceForm(devices=devices)
    if form.validate_on_submit():
        if form.device.data is None:
            flash('Please choose one instrument for analysis.')
        else:
            device_id = form.device.data
            total = {}
            for d in device_id:
                t = timedelta(seconds=0)
                if DeviceUsageLog.query.filter_by(device_id=d).first():
                    d_logs = DeviceUsageLog.query.filter_by(device_id=d).filter(~DeviceUsageLog.remarks.op('regexp')('Not logout')).filter(DeviceUsageLog.start_time <= datetime.utcnow().date()).filter(DeviceUsageLog.start_time >= (datetime.utcnow().date() - timedelta(days=7))).all()
                    device_name = Device.query.filter_by(id=d).first().name
                    for d_log in d_logs:
                        delta = d_log.end_time - d_log.start_time
                        t += delta
                elif GloveBoxLog.query.filter_by(device_id=d).first():
                    g_logs = GloveBoxLog.query.filter_by(device_id=d).filter(~GloveBoxLog.remarks.op('regexp')('Not logout')).filter(GloveBoxLog.start_time <= datetime.utcnow().date()).filter(GloveBoxLog.start_time >= (datetime.utcnow().date() - timedelta(days=7))).all()
                    device_name = Device.query.filter_by(id=d).first().name
                    for g_log in g_logs:
                        delta = g_log.end_time - g_log.start_time
                        t += delta
                else:
                    continue
                total[device_name] = round(t / timedelta(hours=8 * 5) * 100, 2)
            attr = []
            v = []
            for key, value in total.items():
                attr.append(key)
                v.append(value)
            bar = usage_bar(attr, v).render_embed()
    return render_template('analysis/main.html', form=form, gauge=gauge.render_embed(), bar=bar)


def usage_gauge(percentage, angle_range=[225, -45], scale_range=[0, 100], is_legend_show=True):
    gauge = Gauge("Real-time Equipment Usage Percentage")
    gauge.add("Usage Percentage of all Equipments", "Percentage", percentage, angle_range=angle_range, scale_range=scale_range, is_legend_show=is_legend_show)
    return gauge


def usage_bar(attr, v, is_convert=True, mark_line=["min", "max"]):
    bar = Bar("Equipment Usage Time Percentage")
    bar.add("Past 7 Days", attr, v, is_convert=is_convert, mark_line=mark_line, yaxis_label_textsize=8)
    return bar

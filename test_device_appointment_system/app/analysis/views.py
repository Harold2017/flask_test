from . import analysis
from ..models import User, Device, user_device, DeviceUsageLog, GloveBoxLog, DeviceType
from .. import db
from flask import render_template, flash
from datetime import datetime, timedelta
from pytz import timezone
from sqlalchemy import desc
from flask_login import login_required, current_user
from pyecharts import Pie, Line, Overlap, Gauge, Bar, ThemeRiver, Overlap
from pyecharts.utils import json_dumps
from .forms import DeviceForm, DeviceInUseTable
from sqlalchemy.ext.automap import automap_base

tzchina = timezone('Asia/Shanghai')
utc = timezone('UTC')


def days_hours_minutes(td):
    return td.days, td.seconds // 3600, (td.seconds // 60) % 60


@analysis.route('/', methods=['GET', 'POST'])
@login_required
def main():
    devices = Device.query.filter(~Device.name.op('regexp')('test.*')).all()
    cnt = 0
    d_list = []
    devicetypes = DeviceType.query.all()
    Base = automap_base()
    Base.prepare(db.engine,
                 reflect=True)  # use automap of sqlalchemy to get table's corresponding class model
    for d in devices:
        if d.device_inuse is True:
            cnt += 1
            if DeviceUsageLog.query.filter_by(device_id=d.id).first():
                log = DeviceUsageLog.query.filter_by(device_id=d.id).order_by(desc(DeviceUsageLog.id)).first()
                username = log.user_name
            elif GloveBoxLog.query.filter_by(device_id=d.id).first():
                log = GloveBoxLog.query.filter_by(device_id=d.id).order_by(desc(GloveBoxLog.id)).first()
                username = log.user_name
            else:
                log = None
                username = None
                for devicetype in devicetypes:
                    table = getattr(Base.classes, devicetype.type,
                                    None)  # getattr to access attribute like Base.classes.device_type
                    log = db.session.query(table).filter_by(device_id=d.id).order_by(desc(table.id)).first()
                    if log:
                        break
                    else:
                        continue
                if log:
                    username = log.username
            if log:
                d_list.append({
                    "user_name": username,
                    "device_id": log.device_id,
                    "device_name": d.name,
                    "device_status": log.device_status,
                    "start_time": log.start_time.replace(tzinfo=utc).astimezone(tzchina).strftime('%Y/%m/%d-%H:%M:%S'),
                    "material": getattr(log, 'material', 'NA'),
                    "details": log.details
                })
    # print(d_list)
    if len(d_list) == 0:
        inuse_table = None
    else:
        inuse_table = DeviceInUseTable(d_list)
    percentage = round(cnt / len(devices) * 100, 2)
    gauge = usage_gauge(percentage, is_legend_show=False).render_embed()
    '''gauge = {
        "id": gauge.chart_id,
        "width": "100%",
        "height": 600,
        "option": json_dumps(gauge.options)
    }'''
    bar = None

    form = DeviceForm(devices=devices)
    if form.validate_on_submit():
        if form.device.data is None:
            flash('Please choose one instrument for analysis.')
        else:
            device_id = form.device.data
            days = int(form.slider.data)
            total = {}
            for d in device_id:
                t = timedelta(seconds=0)
                if DeviceUsageLog.query.filter_by(device_id=d).first():
                    d_logs = DeviceUsageLog.query.filter_by(device_id=d). \
                        filter(~DeviceUsageLog.remarks.op('regexp')('Not logout')). \
                        filter(DeviceUsageLog.start_time <= datetime.utcnow().date()). \
                        filter(DeviceUsageLog.start_time >= (datetime.utcnow().date() - timedelta(days=days))).all()
                    device_name = Device.query.filter_by(id=d).first().name
                    for d_log in d_logs:
                        delta = d_log.end_time - d_log.start_time
                        t += delta
                elif GloveBoxLog.query.filter_by(device_id=d).first():
                    g_logs = GloveBoxLog.query.filter_by(device_id=d). \
                        filter(~GloveBoxLog.remarks.op('regexp')('Not logout')). \
                        filter(GloveBoxLog.start_time <= datetime.utcnow().date()). \
                        filter(GloveBoxLog.start_time >= (datetime.utcnow().date() - timedelta(days=days))).all()
                    device_name = Device.query.filter_by(id=d).first().name
                    for g_log in g_logs:
                        delta = g_log.end_time - g_log.start_time
                        t += delta
                else:
                    logs = None
                    for devicetype in devicetypes:
                        table = getattr(Base.classes, devicetype.type,
                                        None)  # getattr to access attribute like Base.classes.device_type
                        query = db.session.query(table).filter_by(device_id=d).first()
                        if query:
                            # filter(~table.remarks.op('regexp')('Not logout'))
                            # column.isnot(None) is equal to column != None
                            # but cannot use column is not None or ~(column is None)
                            logs = db.session.query(table).filter_by(device_id=d). \
                                filter(table.end_time.isnot(None)). \
                                filter(table.start_time <= datetime.utcnow().date()). \
                                filter(table.start_time >= (datetime.utcnow().date() - timedelta(days=days))).all()
                            break
                        else:
                            continue
                    device_name = Device.query.filter_by(id=d).first().name
                    if logs is not None and len(logs) != 0:
                        for log in logs:
                            delta = log.end_time - log.start_time
                            t += delta
                    else:
                        t = timedelta(hours=0)
                total[device_name] = [round(t / timedelta(hours=8 * 5 * days / 7) * 100, 2),
                                      round(t / timedelta(hours=1), 2)]
            attr = []
            v = []
            v2 = []
            for key, value in total.items():
                attr.append(key)
                v.append(value[0])
                v2.append(value[1])
            bar = usage_bar(attr, v, v2, days=days).render_embed()
    return render_template('analysis/main.html', form=form, table=inuse_table, gauge=gauge, bar=bar)


def usage_gauge(percentage, angle_range=[225, -45], scale_range=[0, 100], is_legend_show=True):
    gauge = Gauge("Real-time Equipment Usage Percentage")
    gauge.add("Usage Percentage of all Equipments", "Percentage", percentage, angle_range=angle_range,
              scale_range=scale_range, is_legend_show=is_legend_show)
    return gauge


def label_formatter(params):
    return params.value + '%'


def usage_bar(attr, v, v2, is_convert=True, mark_line=["min", "max"], days=7):
    bar = Bar("Equipment Usage", "Bar: time percentage, Line: hours")
    # bar.add("Past "+str(days)+" days", attr, v, is_convert=is_convert, mark_line=mark_line, yaxis_label_textsize=8,
    #  is_label_show=True, label_formatter=label_formatter)
    bar.add("Past " + str(days) + " days", attr, v, is_convert=is_convert, mark_line=mark_line, yaxis_label_textsize=8)
    line = Line()
    line.add("Usage hours", attr, v2)

    overlap = Overlap()
    overlap.add(bar)
    overlap.add(line)
    return overlap


def usage_river(title, classes, data, is_label_show=True):
    tr = ThemeRiver(title)
    tr.add(classes, data, is_label_show=is_label_show)
    return tr

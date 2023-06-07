import pyedflib
import biosppy
import matplotlib.pyplot as plt
from statistics import mean
import pandas as pd
import japanize_matplotlib
from datetime import datetime,timedelta
from scipy.signal import resample
import matplotlib.dates as mdates
import streamlit as st
import tempfile

'''
BPS(Bit Per Second)1秒あたりでリサンプリングする!
'''
st.title("EDFファイルから心拍数を表示")

uploaded_file = st.file_uploader("EDFファイルを選択してください", type=["edf"])
# 開始日時と終了日時
with st.expander("開始日時の設定"):
    start_year = st.text_input('start year')
    start_month = st.text_input('start month')
    start_day = st.text_input('start day')
    start_hour = st.text_input('start hour')
    start_minute = st.text_input('start minute')
    start_second = st.text_input('start second')

with st.expander("終了日時の設定"):
    end_year = st.text_input('end year')
    end_month = st.text_input('end month')
    end_day = st.text_input('end day')
    end_hour = st.text_input('end hour')
    end_minute = st.text_input('end minute')
    end_second = st.text_input('end second')



if uploaded_file is not None:
   with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file.flush()

        #基本設定
        filename = tmp_file.name


        start_datetime = datetime(int(start_year), int(start_month), int(start_day), int(start_hour), int(start_minute), int(start_second))
        end_datetime = datetime(int(end_year), int(end_month), int(end_day), int(end_hour), int(end_minute), int(end_second))


        file = pyedflib.EdfReader(filename)

        # ECGデータが含まれるチャンネルを特定
        def find_ecg_channel(file):
            # EDFファイル内のすべてのチャンネルラベルを取得する
            channel_labels = file.getSignalLabels()
            # ECGデータが含まれるチャンネルを特定する
            for i, label in enumerate(channel_labels):
                if 'ECG' in label:
                    return i
            # ECGデータが含まれるチャンネルが見つからない場合は、Noneを返す
            return None

        def detect_heart_rate(signal, sampling_rate):
            out = biosppy.signals.ecg.ecg(signal, sampling_rate=sampling_rate,show=False,interactive=False)
            # HeartRateの基準時間とHeartRateのデータのインデックスを返す
            return out['heart_rate_ts'],out['heart_rate']



        ecg_channel = find_ecg_channel(file)

        if ecg_channel is not None:
            # チャンネルから信号とサンプリングレートを取得
            signal = file.readSignal(ecg_channel)
            sampling_rate = file.getSampleFrequency(ecg_channel)
            print('sampling rate',sampling_rate)
            
            #信号の軸とHeartRateの取得
            ts,heart_rate = detect_heart_rate(signal, sampling_rate)
            print('ts',ts)
            print('heart rate',heart_rate)
            print('bpm',len(heart_rate))

            # オリジナルのデータの長さとサンプリングレートを取得
            original_length = len(ts)
            original_sampling_rate = original_length / ts[-1]
            #1秒あたりでサンプリングレート
            sampling_rate =1
            # 新しいデータの長さを計算
            new_length = int(original_length * (sampling_rate / original_sampling_rate))

            # ダウンサンプリング
            downsampled_ts = resample(ts, new_length)
            downsampled_heart_rate= resample(heart_rate, new_length)

        #ダウンサンプリングされた値をdatetimeの形に直す
            datetimes = []
            for i,value in enumerate(downsampled_ts):
                datetimes.append(start_datetime + timedelta(seconds=i))
            datetimes = [value.strftime('%Y-%m-%d %H:%M:%S') for value in datetimes]

            #pandasの形に直す
            heart_rate_df = pd.DataFrame(downsampled_heart_rate)
            heart_rate_df = heart_rate_df.set_index(pd.to_datetime(datetimes))

        else:
            print('心拍データが含まれていません')
        #グラフを表示する領域を，figオブジェクトとして作成。
        fig = plt.figure(figsize = (10,6), facecolor='lightblue')
        ax = fig.add_subplot()
        ax.plot(heart_rate_df)

        #axのx軸ラベルを指定
        # 5分ごとの日時をリストに格納
        time_range_5min = []
        current_time = start_datetime
        while current_time <= end_datetime:
            time_range_5min.append(current_time)
        #minutesを変えることで、何分ごとにx軸を表示するかを決める
            current_time += timedelta(minutes=5)
        # datetimeオブジェクトを数値に変換
        time_range_5min_num = [mdates.date2num(dt) for dt in time_range_5min]
        # x軸の目盛りを設定
        ax.set_xticks(time_range_5min_num)
        # x軸のフォーマッタを設定
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))

        #各subplotにxラベルを追加
        ax.set_xlabel('time')
        #各subplotにyラベルを追加
        ax.set_ylabel('bpm(1m)')
        st.pyplot()
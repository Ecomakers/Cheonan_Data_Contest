import pandas as pd
import numpy as np
import streamlit as st
import geopandas as gpd
import plotly.express as px
import json
import plotly.graph_objects as go

st.set_page_config(layout="wide")

# 데이터 로드 함수
def load_data(path):
    data = pd.read_csv(path, encoding='euc-kr')
    return data

# 메인 함수
def main():
    st.title('🐕‍🦺천안시 반려견 산책로 조성')
    
    # 데이터 로드
    data = load_data('final_data.csv')
    gdf = gpd.GeoDataFrame(data, geometry=gpd.GeoSeries.from_wkt(data['geometry']))
    
    # 사이드바에서 선택 박스 추가
    st.sidebar.header('선택 옵션')
    
    # EMD_KOR_NM 열의 고유 값 가져오기
    options = ['전체'] + list(np.unique(gdf['EMD_KOR_NM']))
    
    # 드롭다운 메뉴 생성 (사이드바)
    selected_option = st.sidebar.selectbox('지역을 선택해주세요', options, index=2)
    
    # 선택된 값으로 데이터 필터링
    if selected_option == '전체': 
        filtered_data = gdf
    else:
        filtered_data = gdf[gdf['EMD_KOR_NM'] == selected_option]
    
    # 선택된 지역의 중심 좌표 계산
    if not filtered_data.empty:
        centroid = filtered_data.geometry.centroid
        center_lat, center_lon = centroid.y.mean(), centroid.x.mean()
    else:
        center_lat, center_lon = 36.8, 127.1  # 기본 좌표 (천안시의 중심 좌표로 설정)
        
    zoom_size = 11
    if len(filtered_data) <= 100:
        zoom_size = 14
    elif len(filtered_data) <= 1000:
        zoom_size = 13
    elif len(filtered_data) <= 5000:
        zoom_size = 12
    
    # 탭 생성
    tab1, tab2, tab3 = st.tabs(['🗺️ 산책로 추천', '🌏 항목 지도', '🔎 지역비교'])
    
    with tab1:
        st.write(f'선택된 지역: {selected_option}')
        
        # 로딩 화면 표시
        with st.spinner('지도를 로딩 중입니다...(20~30초 소요)'):
            # GeoDataFrame을 GeoJSON 형식으로 변환
            geojson = json.loads(filtered_data.to_json())
    
            # Plotly Choropleth Mapbox 생성
            fig = px.choropleth_mapbox(
                filtered_data, 
                geojson=geojson, 
                locations='gid', 
                featureidkey="properties.gid", 
                color='y', 
                color_continuous_scale="OrRd",  
                mapbox_style="carto-positron", 
                zoom=zoom_size, 
                center={"lat": center_lat, "lon": center_lon}, 
                opacity=0.5,
                labels={'y':'산책지수'},
                hover_name='EMD_KOR_NM'
            )
    
            # EMD_KOR_NM 별로 그룹화하여 격자 연결
            for emd_name in filtered_data['EMD_KOR_NM'].unique():
                emd_data = filtered_data[(filtered_data['EMD_KOR_NM'] == emd_name) & filtered_data['link_order'].notnull()]
                emd_data = emd_data.sort_values('link_order')
                
                if not emd_data.empty:
                    centroids = emd_data.geometry.centroid
                    coords = list(zip(centroids.x, centroids.y))
                    
                    fig.add_trace(go.Scattermapbox(
                        mode='lines',
                        lon=[coord[0] for coord in coords],
                        lat=[coord[1] for coord in coords],
                        line=dict(width=3, color='black'),
                        showlegend=False,  # Legend를 숨기기 위해 추가
                        name=f'{emd_name} 추천 산책로'
                    ))
        
            fig.update_layout(
                mapbox_accesstoken="your_mapbox_access_token",
                title="반려견 산책 지정",
                margin={"r":0,"t":0,"l":0,"b":0}
            )
    
            # Streamlit에 Plotly 차트를 표시
            st.plotly_chart(fig, use_container_width=True)
            
            st.write("""** 전체적으로 산책지수가 너무 낮아 산책로 개발이 불가능한 지역은 산책로를 추천하지 않음  
                           (광덕면, 동면, 목천읍, 병천면, 북면, 성거읍, 성남면, 성환읍, 수신면, 신당동, 안서동, 업성동, 유량동, 입장면, 직산읍, 차암동)""")
        
    with tab2:
        
        # point_gpd 데이터 로드
        point_df = load_data('point_gpd.csv')
        point_gpd = gpd.GeoDataFrame(point_df, geometry=gpd.points_from_xy(point_df['경도'], point_df['위도']))

        # 항목의 고유 값 가져오기
        features = point_gpd['항목'].unique()
        
        # multiselect 박스 생성
        feature_select = st.multiselect('항목을 선택해주세요(복수선택가능)', features, default=features[0])

        # 선택된 항목으로 데이터 필터링
        filtered_points = point_gpd[point_gpd['항목'].isin(feature_select)]
        
        # 지도 생성
        fig = px.scatter_mapbox(
            filtered_points, 
            lat=filtered_points.geometry.y, 
            lon=filtered_points.geometry.x, 
            hover_name='세부항목', 
            color='항목',
            mapbox_style="carto-positron",
            zoom=zoom_size,
            center={"lat": center_lat, "lon": center_lon}
        )

        fig.update_layout(
            mapbox_accesstoken="your_mapbox_access_token",
            title="선택된 항목의 위치",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        # 지도 출력
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        op2 = list(np.unique(gdf['EMD_KOR_NM']))

        # 지역 선택 박스 생성
        compare_option = st.selectbox('비교할 지역을 선택해주세요', op2)

        compare_data = gdf[gdf['EMD_KOR_NM'] == compare_option]
        compare_avg = compare_data.groupby(['EMD_KOR_NM'])[compare_data.columns[3:-1]].mean().reset_index() if not compare_data.empty else pd.DataFrame()

        if selected_option == '전체':
            df = pd.DataFrame(filtered_data.mean()).T
            df['EMD_KOR_NM'] = '전체'
            selected_avg = df[['EMD_KOR_NM', '총인구', '유소년(청소년)인구비율', '교통cctv', '방범cctv', '보안등', '가로등', '공원', '산책로',
                               '반려견_동반문화시설', '학원_교습소', '아파트밀도', '학교', '상가밀도', '주점', 'y']]
        else:
            selected_avg = filtered_data.groupby(['EMD_KOR_NM'])[filtered_data.columns[3:-1]].mean().reset_index() if not filtered_data.empty else pd.DataFrame()

        total_df = pd.concat([selected_avg, compare_avg])
        total_df.rename(columns={'y':'산책지수'}, inplace=True)

        # Wide에서 Long 형식으로 변환
        long_df = pd.melt(
            total_df,
            id_vars=['EMD_KOR_NM'],  # 고정된 열 (지역)
            var_name='항목',  # 변수가 될 열의 이름
            value_name='값'  # 값이 될 열의 이름
        )

        # Bar plot 생성
        fig = px.bar(
            long_df,
            x='항목',  # x축: 데이터 열들
            y='값',  # y축: 값
            color='EMD_KOR_NM',  # 색상: 지역
            barmode='group',
            title='지역별 데이터 비교',
            labels={'값': '값', '항목': '항목'},
            height=600,
            color_discrete_sequence=['#1f77b4', '#ff7f0e']
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.write("※ 위 수치는 100m * 100m 격자의 평균값 입니다.")
        st.write("※ 확대해서 보고싶은 곳을 드래그하면 확대됩니다.")



# 앱 실행
if __name__ == "__main__":
    main()

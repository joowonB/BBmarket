if (navigator.geolocation) {
  navigator.geolocation.getCurrentPosition(
    function (position) {
      var userLat = position.coords.latitude;
      var userLng = position.coords.longitude;

      // 카카오 지도 객체 생성
      var map = new kakao.maps.Map(document.getElementById("map"), {
        center: new kakao.maps.LatLng(userLat, userLng),
        level: 5,
      });

      var clusterer = new kakao.maps.MarkerClusterer({
        map: map,
        averageCenter: true,
        minLevel: 2,
      });

      // 사용자의 현재 위치를 표시할 마커 생성
      var userMarker = new kakao.maps.Marker({
        position: new kakao.maps.LatLng(userLat, userLng),
        map: map,
        title: "내 위치",
      });

      var userInfoWindow = new kakao.maps.InfoWindow({
        content: '<div style="padding:5px;">사용자 위치</div>',
        removable: true,
      });

      kakao.maps.event.addListener(userMarker, "click", function () {
        userInfoWindow.open(map, userMarker);
      });

      // JSON 파일에서 데이터 가져오기
      $.getJSON(jsonDataUrl, function (data) {
        var currentInfoWindow = null;

        // 각 상품 위치에 대한 마커 배열 생성
        var markers = data
          .filter(function (position) {
            // 필수 데이터가 존재하는 항목만 필터링
            return position.product_id && position.product.product_image_url;
          })
          .map(function (position) {
            var marker = new kakao.maps.Marker({
              position: new kakao.maps.LatLng(position.latitude, position.longitude),
            });

            // 제품 상세 페이지 링크 생성
            var productLink = "/product/" + position.product_id;

            // 인포윈도우 내용 생성
            var iwContent = `
              <div style="padding:10px;">
                <a href="${productLink}" target="_blank">
                  <img src="${position.product_image_url}" style="width:100px;height:100px;">
                </a><br>
                <strong>${position.product_name}</strong><br>
                <em>판매자: ${position.user_name}</em><br>
                <span>주소: ${position.address}</span><br>
                <a href="${productLink}" target="_blank" class="product-link">상품 상세보기</a>
              </div>`;

            var clickInfowindow = new kakao.maps.InfoWindow({
              content: iwContent,
              removable: true,
            });

            // 마커 클릭 이벤트 등록
            kakao.maps.event.addListener(marker, "click", function () {
              // 다른 인포윈도우가 열려 있으면 닫기
              if (currentInfoWindow) {
                currentInfoWindow.close();
              }
              // 현재 클릭된 마커의 인포윈도우 열기
              clickInfowindow.open(map, marker);
              currentInfoWindow = clickInfowindow; // 현재 열린 인포윈도우를 저장
            });

            return marker;
          });

        // 클러스터러에 마커 추가
        clusterer.addMarkers(markers);
      }).fail(function () {
        alert("JSON 데이터를 불러오는데 실패했습니다.");
      });
    },
    function (error) {
      alert("GPS 정보를 가져오는데 실패했습니다.");
    }
  );
} else {
  alert("브라우저에서 GPS를 지원하지 않습니다.");
}

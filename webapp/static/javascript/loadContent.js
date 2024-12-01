let currentPage = 1;
const itemsPerPage = 10;
let currentType = "product"; // 현재 로드된 타입을 저장하는 변수

async function loadContent(type) {
  currentType = type; // 현재 로드된 타입 업데이트
  const contentArea = document.getElementById("content-area");
  const pageTitle = document.getElementById("page-title");

  if (type === "product") {
    pageTitle.innerHTML = "상품 관리";

    // 관리자 전용 상품 목록 API 호출
    const response = await fetch("/api/admin/products/");
    const products = await response.json();

    // 총 페이지 수 계산
    const totalPages = Math.ceil(products.length / itemsPerPage);

    // 현재 페이지에 해당하는 상품 데이터 추출
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentItems = products.slice(startIndex, endIndex);

    // 상품 목록을 테이블로 생성
    let productTable = `
      <div class="frame-22">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>상품명</th>
              <th>설명</th>
              <th>가격</th>
              <th>삭제</th>
            </tr>
          </thead>
          <tbody>
    `;

    // 현재 페이지의 상품 데이터를 테이블 행으로 추가
    currentItems.forEach((product) => {
      productTable += `
        <tr id="product-${product.id}">
          <td>${product.id}</td>
          <td>${product.product_name}</td>
          <td>${product.product_description}</td>
          <td>${product.product_price}</td>
          <td><button onclick="deleteProduct(${product.id})">삭제</button></td>
        </tr>
      `;
    });

    productTable += `
          </tbody>
        </table>
        <div class="pagination">
          ${
            currentPage > 1
              ? `<button onclick="changePage(${currentPage - 1})">이전</button>`
              : ""
          }
          ${renderPageNumbers(totalPages)}
          ${
            currentPage < totalPages
              ? `<button onclick="changePage(${currentPage + 1})">다음</button>`
              : ""
          }
        </div>
      </div>
    `;

    // contentArea에 생성된 테이블을 삽입
    contentArea.innerHTML = productTable;
  } else if (type === "stats") {
    pageTitle.innerHTML = "통계 현황";

    // 오늘 업로드된 상품 수 API 호출
    const responseTodayCount = await fetch("/api/admin/today-uploaded-count/");
    const todayCountData = await responseTodayCount.json();
    const todayUploadedCount = todayCountData.count; // 오늘 업로드된 상품 수

    const responseRecentProducts = await fetch("/api/admin/recent-products/");
    const recentProducts = await responseRecentProducts.json();

    const responseSignupCount = await fetch("/api/admin/today-signup-count/");
    const signupData = await responseSignupCount.json();

    contentArea.innerHTML = `<!-- 통계 현황 콘텐츠 -->
      <div class="stats-uproad">
        <div class="stats-title">실시간 상품 업로드 현황</div>
        <div class="stats-line"></div>
        <ul class="recent-products-list">
          ${recentProducts
            .map(
              (product) => `
          <li class="product-item">
              <strong>${product.product_name || "상품 이름 없음"}</strong> - ${
                product.product_price || "가격 정보 없음"
              }원 <br>
              <span>${product.product_description || "설명 없음"}</span> <br>
              <em>업로드 날짜: ${
                product.product_created_at
                  ? new Date(product.product_created_at).toLocaleDateString()
                  : "날짜 정보 없음"
              }</em>
          </li>
              `
            )
            .join("")}
        </ul>
      </div>
      <div class="stats-category-graph">
        <div class="stats-category-title">카테고리 순위</div>
        <canvas id="categoryChart"></canvas> <!-- 차트를 그릴 캔버스 추가 -->
      </div>

        <div class="stats-today">
          <div class="stats-today-header">
          <div class="stats-today-title">금일상품업로드</div>
          </div>
        <div class="stats-today-count">
        오늘 업로드된 상품 개수: <span id="today-uploaded-count">${todayUploadedCount}</span>
        </div>

        <div class="stats-visit-today">
          <div class="stats-visit-title">금일 방문수</div>
        </div>
        <div class="stats-frame-3"></div>
        <div class="stats-signup-today">
          <div class="stats-signup-title">금일 가입수</div>
        </div>
        <div class="stats-frame-4">${
          signupData.today_signup_count || 0
        }명</div> <!-- 오늘 가입자 수 -->
      </div>
      <div class="stats-user-trend">
        <div class="stats-trend-title">가입 회원 추이</div>
        <canvas id="signupTrendChart"></canvas> <!-- 가입 추이를 위한 차트 -->
      </div>
    `;

    // 금일 방문 수 API 호출
    const responseVisitCount = await fetch("/api/admin/today-visited-count/");
    const visitData = await responseVisitCount.json();

    // stats-frame-3에 금일 방문수 삽입
    const visitCountDisplay = document.createElement("div");
    visitCountDisplay.innerHTML = `<strong>금일 방문수: ${visitData.today_visited_count}</strong>`;
    document.querySelector(".stats-frame-3").appendChild(visitCountDisplay);

    // 최근 7일 가입자 수 API 호출
    const responseWeeklySignupTrend = await fetch(
      "/api/admin/weekly-signup-trend/"
    );
    const signupTrendData = await responseWeeklySignupTrend.json();
    const weeklySignupCounts = signupTrendData.weekly_signup_counts;

    const ctxTrend = document
      .getElementById("signupTrendChart")
      .getContext("2d");

    const labels = [...Array(7).keys()]
      .map((i) => {
        const date = new Date(Date.now() - i * 864e5);
        return date.toISOString().split("T")[0];
      })
      .reverse(); // 날짜를 역순으로 정렬

    // 데이터와 라벨을 모두 역순으로 정렬
    const data = weeklySignupCounts.slice().reverse();

    const signupTrendChart = new Chart(ctxTrend, {
      type: "line",
      data: {
        labels: labels, // 라벨과 데이터의 크기가 동일해야 함
        datasets: [
          {
            label: "가입자 수",
            data: data,
            borderColor: "rgba(75, 192, 192, 1)",
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            fill: true,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });

    // 카테고리와 상품 개수 데이터를 불러오는 API 호출
    const responseCategoryCount = await fetch(
      "/api/admin/category-product-count/"
    );
    const categories = await responseCategoryCount.json();

    // 차트 데이터 준비
    const categoryNames = categories.map((c) => c.category_name);
    const productCounts = categories.map((c) => c.product_count);

    // Chart.js를 사용하여 차트 그리기
    const ctx = document.getElementById("categoryChart").getContext("2d");
    const categoryChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: categoryNames,
        datasets: [
          {
            label: "상품 개수",
            data: productCounts,
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 1,
          },
        ],
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
          },
        },
      },
    });
  } else if (type === "user") {
    pageTitle.innerHTML = "회원 관리";

    // 모든 사용자 정보 API 호출
    const response = await fetch("/api/admin/users/");
    const users = await response.json();

    // 총 페이지 수 계산
    const totalPages = Math.ceil(users.length / itemsPerPage);

    // 현재 페이지에 해당하는 사용자 데이터 추출
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const currentItems = users.slice(startIndex, endIndex);

    // 사용자 목록을 테이블로 생성
    let userTable = `
      <div class="frame-22">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>사용자명</th>
              <th>이메일</th>
              <th>이름</th>
              <th>전화번호</th>
              <th>주소</th>
              <th>삭제</th>
            </tr>
          </thead>
          <tbody>
    `;

    // 현재 페이지의 사용자 데이터를 테이블 행으로 추가
    currentItems.forEach((user) => {
      userTable += `
        <tr id="user-${user.user_id}">
          <td>${user.user_id}</td>
          <td>${user.user_userid}</td>
          <td>${user.user_email}</td>
          <td>${user.user_name}</td>
          <td>${user.user_phoneNum}</td>
          <td>${user.user_address}</td>
          <td><button onclick="deleteUser(${user.user_id})">탈퇴</button></td>
        </tr>
      `;
    });

    userTable += `
          </tbody>
        </table>
        <div class="pagination">
          ${
            currentPage > 1
              ? `<button onclick="changePage(${currentPage - 1})">이전</button>`
              : ""
          }
          ${renderPageNumbers(totalPages)}
          ${
            currentPage < totalPages
              ? `<button onclick="changePage(${currentPage + 1})">다음</button>`
              : ""
          }
        </div>
      </div>
    `;

    // contentArea에 생성된 테이블을 삽입
    contentArea.innerHTML = userTable;
  }
}

// 페이지 번호를 렌더링하는 함수
function renderPageNumbers(totalPages) {
  let pageNumbers = "";
  for (let i = 1; i <= totalPages; i++) {
    if (i === currentPage) {
      pageNumbers += `<span>${i}</span>`; // 현재 페이지는 클릭할 수 없는 span으로 표시
    } else {
      pageNumbers += `<button onclick="changePage(${i})">${i}</button>`; // 다른 페이지는 버튼으로 표시
    }
  }
  return pageNumbers;
}

// 페이지 변경 함수
function changePage(page) {
  currentPage = page;
  loadContent(currentType); // 현재 로드된 타입에 따라 로드
}

// 상품 삭제 함수
async function deleteProduct(productId) {
  const response = await fetch(`/api/admin/products/${productId}/delete/`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': getCSRFToken(), // CSRF 토큰 추가
    },
  });

  if (response.ok) {
    document.getElementById(`product-${productId}`).remove(); // 삭제 성공 시 해당 행 제거

    // geocode.py 실행 요청
    triggerGeocode();
  } else {
    alert('상품 삭제에 실패했습니다.'); // 실패 시 알림
  }
}

// 사용자 삭제 함수
async function deleteUser(userId) {
  const response = await fetch(`/api/admin/users/${userId}/delete/`, {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': getCSRFToken(), // CSRF 토큰 추가
    },
  });

  if (response.ok) {
    document.getElementById(`user-${userId}`).remove(); // 삭제 성공 시 해당 행 제거

    // geocode.py 실행 요청
    triggerGeocode();
  } else {
    alert('사용자 삭제에 실패했습니다.'); // 실패 시 알림
  }
}

// geocode.py 실행 트리거
async function triggerGeocode() {
  try {
    const response = await fetch('/execute-geocode/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCSRFToken(), // CSRF 토큰 추가
      },
    });

    if (!response.ok) {
      console.error('Geocode 실행 실패:', await response.text());
    }
  } catch (error) {
    console.error('Geocode 실행 중 오류 발생:', error);
  }
}

// CSRF 토큰 가져오는 함수
function getCSRFToken() {
  return document.cookie
    .split("; ")
    .find((row) => row.startsWith("csrftoken="))
    .split("=")[1];
}

// 페이지가 로드될 때 기본 콘텐츠로 'product'를 불러옵니다.
window.onload = function () {
  loadContent("product");
};

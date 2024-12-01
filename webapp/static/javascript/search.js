// 검색 버튼 클릭 이벤트
document.getElementById("searchButton").addEventListener("click", function () {
  const searchValue = document.getElementById("searchInput").value;
  if (searchValue) {
    window.location.href = `/search?q=${searchValue}`;
  } else {
    alert("검색어를 입력하세요.");
  }
});

// 엔터 키 입력 시 검색
document
  .getElementById("searchInput")
  .addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault(); // 기본 이벤트를 막아 중복 검색을 방지
      const searchValue = document.getElementById("searchInput").value;
      if (searchValue) {
        window.location.href = `/search?q=${searchValue}`;
      } else {
        alert("검색어를 입력하세요.");
      }
    }
  });

// 현재 선택된 자동 완성 항목을 추적하는 변수
let currentIndex = -1;

// 자동 완성 기능을 실행하는 함수
function showSuggestions(query) {
  const suggestionsBox = document.getElementById("suggestions");
  if (query.length > 0) {
    fetch(`/autocomplete?q=${query}`)
      .then((response) => response.json())
      .then((data) => {
        let suggestionHTML = "<ul>";
        data.results.forEach((item) => {
          suggestionHTML += `
            <li 
              class="suggestion-item" 
              onclick="selectSuggestion('${item.product_name}')"
              data-index="${data.results.indexOf(item)}">
              ${item.product_name}
            </li>`;
        });
        suggestionHTML += "</ul>";
        suggestionsBox.innerHTML = suggestionHTML;
        suggestionsBox.style.display = "block";
      })
      .catch((error) => console.error("Error fetching suggestions:", error));
  } else {
    suggestionsBox.style.display = "none";
  }
}

// 사용자가 자동 완성 항목을 클릭할 때 호출되는 함수
function selectSuggestion(productName) {
  document.getElementById("searchInput").value = productName;
  document.getElementById("suggestions").style.display = "none";
}

// 키보드 방향키 및 Enter 키 이벤트
document
  .getElementById("searchInput")
  .addEventListener("keydown", function (e) {
    const suggestionsBox = document.getElementById("suggestions");
    const items = suggestionsBox.querySelectorAll(".suggestion-item");

    if (items.length > 0) {
      // 아래 방향키
      if (e.key === "ArrowDown") {
        e.preventDefault();
        currentIndex = (currentIndex + 1) % items.length;
        highlightSuggestion(items, currentIndex);
      }

      // 위 방향키
      else if (e.key === "ArrowUp") {
        e.preventDefault();
        currentIndex = (currentIndex - 1 + items.length) % items.length;
        highlightSuggestion(items, currentIndex);
      }

      // Enter 키
      else if (e.key === "Enter" && currentIndex > -1) {
        e.preventDefault();
        items[currentIndex].click(); // 선택된 항목을 클릭하여 검색 실행
      }
    }
  });

// 선택된 항목을 강조 표시하는 함수
function highlightSuggestion(items, index) {
  items.forEach((item, i) => {
    if (i === index) {
      item.classList.add("highlighted");
    } else {
      item.classList.remove("highlighted");
    }
  });
}

// 클릭 시 자동 완성 창을 닫음 (다른 곳 클릭할 경우)
document.addEventListener("click", function (e) {
  const suggestionsBox = document.getElementById("suggestions");
  if (!document.getElementById("searchInput").contains(e.target)) {
    suggestionsBox.style.display = "none";
  }
});

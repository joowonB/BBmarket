document.addEventListener("DOMContentLoaded", function () {
    const imageUpload = document.getElementById("imageUpload");

    if (imageUpload) {
        // 이미지 업로드 이벤트 리스너 추가
        imageUpload.addEventListener("change", function (event) {
            const file = event.target.files[0];
            if (file) {
                // 이미지 미리보기 표시
                const reader = new FileReader();
                reader.onload = function (e) {
                    document.getElementById("userImage").src = e.target.result;
                };
                reader.readAsDataURL(file);

                // FormData에 이미지 파일 추가
                const formData = new FormData();
                formData.append("image", file);

                // CSRF 토큰 가져오기
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                // 서버에 예측 요청 보내기
                fetch("/predict-category/", {
                    method: "POST",
                    body: formData,
                    headers: {
                        "X-CSRFToken": csrftoken,
                    },
                })
                .then(response => response.json())
                .then(data => {
                    console.log("예측된 데이터:", data);
                    const probabilities = data.probabilities;
                    const bestCategory = data.best_category;

                    // 모든 카테고리를 0.00%로 초기화한 후 서버 응답으로 업데이트
                    const categoryItems = document.querySelectorAll("#categoryProbabilities .category-item");
                    categoryItems.forEach((item, index) => {
                        const categoryName = `카테고리${index + 1}`;
                        const percentage = (probabilities[categoryName] * 100).toFixed(2) || "0.00";

                        // 업데이트된 확률 표시
                        item.querySelector(".progress-fill").style.width = `${percentage}%`;
                        item.querySelector(".percentage-text").textContent = `${percentage}%`;
                    });

                    // 드롭다운에서 예측된 카테고리를 기본 선택값으로 설정
                    const categoryDropdown = document.getElementById("categoryDropdown");
                    for (const option of categoryDropdown.options) {
                        if (option.text === bestCategory) {
                            option.selected = true;
                            // 예측된 카테고리를 selectedCategory에 표시
                            const selectedCategory = document.getElementById("selectedCategory");
                            if (selectedCategory) {
                                selectedCategory.textContent = bestCategory;
                                console.log("선택된 카테고리:", bestCategory);
                            } else {
                                console.error("#selectedCategory 요소를 찾을 수 없습니다.");
                            }
                            break;
                        }
                    }
                })
                .catch(error => console.error("Error:", error));
            }
        });
    } else {
        console.error("#imageUpload 요소를 찾을 수 없습니다.");
    }
});

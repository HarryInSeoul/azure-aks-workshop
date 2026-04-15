use crate::configuration::Settings;
use crate::model::Product;

pub fn fetch_products(_settings: &Settings) -> Vec<Product> {
    vec![
        Product {
            id: 1,
            name: "콘토소 캣닢 친구".to_string(),
            price: 9.99,
            description: "콘토소 캣닢 친구 장난감과 함께 고양이의 낚시 모험을 지켜보세요. 거부할 수 없는 캣닢과 흔들리는 물고기 미끼가 가득합니다.".to_string(),
            image: "/catnip.jpg".to_string()
        },
        Product {
            id: 2,
            name: "짭짤한 선원의 삑삑 오징어".to_string(),
            price: 6.99,
            description: "짭짤한 선원의 삑삑 오징어와 함께 반려견의 항해를 시작하세요. 여러 개의 삑삑이와 바스락거리는 촉수가 있는 인터랙티브 장난감입니다.".to_string(),
            image: "/squid.jpg".to_string()
        },
        Product {
            id: 3,
            name: "인어공주 쥐돌이 3형제".to_string(),
            price: 12.99,
            description: "인어공주 쥐돌이 3형제로 고양이를 즐겁게 해주세요. 인어 옷을 입은 사랑스러운 봉제 쥐에 캣닢이 가득 차 호기심을 자극합니다.".to_string(),
            image: "/mermaid.jpg".to_string()
        },
        Product {
            id: 4,
            name: "바다 탐험가 퍼즐볼".to_string(),
            price: 11.99,
            description: "바다 탐험가 퍼즐볼로 반려동물의 문제 해결 능력에 도전하세요. 숨겨진 칸과 간식이 있어 두뇌 자극과 재미를 동시에 제공합니다.".to_string(),
            image: "/ocean.jpg".to_string()
        },
        Product {
            id: 5,
            name: "해적 앵무새 낚싯대".to_string(),
            price: 8.99,
            description: "해적 앵무새 낚싯대로 고양이와 즐거운 놀이를 즐기세요. 화려한 깃털과 딸랑이 방울이 해적 앵무새의 장난스러운 매력을 재현합니다.".to_string(),
            image: "/pirate.jpg".to_string()
        },
        Product {
            id: 6,
            name: "뱃사람의 터그 로프".to_string(),
            price: 14.99,
            description: "뱃사람의 터그 로프로 줄다리기와 해양 모험을 동시에! 해양용 로프로 만들어져 인터랙티브 놀이와 반려견 치아 건강 증진에 완벽합니다.".to_string(),
            image: "/tug.jpg".to_string()
        },
        Product {
            id: 7,
            name: "조개 포근 침대".to_string(),
            price: 19.99,
            description: "조개 포근 침대로 반려동물에게 아늑한 공간을 선물하세요. 조개 모양의 푹신한 침대가 고양이와 소형견에게 편안한 휴식을 제공합니다.".to_string(),
            image: "/bed.jpg".to_string()
        },
        Product {
            id: 8,
            name: "해양 매듭 공".to_string(),
            price: 7.99,
            description: "해양 매듭 공으로 반려견의 내면의 선원을 깨워보세요. 튼튼한 로프로 만들어져 던지기, 당기기, 씹기 놀이에 안성맞춤입니다.".to_string(),
            image: "/knot.jpg".to_string()
        },
        Product {
            id: 9,
            name: "콘토소 집게발 꽃게 장난감".to_string(),
            price: 3.99,
            description: "콘토소 집게발 꽃게 장난감에 고양이가 열광하는 모습을 지켜보세요. 바스락거리는 소재와 캣닢이 사냥 본능을 깨워 끝없는 재미를 선사합니다.".to_string(),
            image: "/crabby.jpg".to_string()
        },
        Product {
            id: 10,
            name: "어이 강아지 구명조끼".to_string(),
            price: 5.99,
            description: "어이 강아지 구명조끼로 물놀이 시 반려견의 안전을 지켜주세요. 강아지를 위해 설계된 부력 조끼로 스타일리시하게 안전과 가시성을 확보합니다.".to_string(),
            image: "/lifejacket.jpg".to_string()
        }
    ]
}

import streamlit as st
import json
import openai
from pydantic import BaseModel, Field

from serpapi import GoogleSearch

GoogleSearch.SERP_API_KEY = st.secrets["SERPAPI_API_KEY"]

PROMPT_TEMPLATE = """あなたは様々な飲食店を知りつくす専門家です。下記条件を満たす飲食店をできるだけ多く教えて。
料理: {dish}
近くの場所: {location}
"""


class Place(BaseModel):
    title: str = Field(description="店名", examples=["サイゼリヤ 渋谷店"])
    description: str = Field(description="説明", examples=["コスパ最強"])
    type: str = Field(description="営業形態", examples=["レストラン"])
    thumbnail: str = Field(description="画像リンク")

    # Place
    address: str = Field(description="住所")
    place_id: str = Field(description="place ID")
    place_id_search: str = Field(description="SerpApi 検索リンク")

    # Review
    rating: float = Field(description="評価", examples=[3.5])
    reviewCount: int = Field(description="レビュー数", examples=[1000])


class Places(BaseModel):
    places: list[Place]


OUTPUT_FUNCTION_PLACES = {
    "name": "output_function_place",
    "description": "飲食店を検索する",
    "parameters": Places.schema(),
}


class SearchPlaceParams:
    def __init__(self, dish, loc, limit):
        self.engine = "google_local"
        self.language = "ja"
        self.num = limit
        self.query = dish + " " + loc
        # self.dish = dish
        # self.location = loc


def searchPlacesWithParams(params: SearchPlaceParams):
    reqParams = {
        "engine": params.engine,
        "hl": params.language,
        "num": params.num,
        "q": params.query,
        # "location": "Shibuya, Tokyo, Japan",
    }

    res = GoogleSearch(reqParams)
    resDict = res.get_dict()
    assert resDict.get("error") == None

    return resDict["local_results"]


# UI
st.title("食事処提案 AI")
inputDish = st.text_input(label="食べたい料理は？")
inputLoc = st.text_input(label="場所は？")


# Logic
if inputDish and inputLoc:
    with st.spinner(text="生成中..."):
        # places = searchPlacesWithParams(SearchPlaceParams(inputDish, inputLoc, 10))
        # st.write(places)

        messages = [
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(dish=inputDish, location=inputLoc),
            },
        ]
        res = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            functions=[OUTPUT_FUNCTION_PLACES],
            function_call={"name": OUTPUT_FUNCTION_PLACES["name"]},
        )

        # st.write(res)

        funcCallArgs = res["choices"][0]["message"]["function_call"]["arguments"]
        placeDict = json.loads(funcCallArgs)

        # st.write(placeDict)

        placeMarkdown = "## 食事処\n"
        for i, place in enumerate(placeDict["places"]):
            placeMarkdown += f"{i+1}. {place}\n"

        st.write(placeMarkdown)

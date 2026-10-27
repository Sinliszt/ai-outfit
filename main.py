import streamlit as st
from recommender import generate_ranked_outfits, score_outfit

st.set_page_config(page_title="Closet AI", page_icon="👗", layout="wide")

st.title("Closet AI")

if "wardrobe" not in st.session_state:
    st.session_state.wardrobe = []
if "saved_outfits" not in st.session_state:
    st.session_state.saved_outfits = []
if "ratings" not in st.session_state:
    st.session_state.ratings = {}

CATEGORIES = ["Top", "Bottom", "Dress", "Shoes", "Outerwear", "Accessory"]
COLOURS = [
    "Black", "White", "Grey", "Beige", "Cream", "Brown", "Navy", "Blue",
    "Light blue", "Green", "Olive", "Red", "Pink", "Purple", "Yellow",
    "Orange", "Denim blue", "Multicolour", "Other"
]
STYLES = ["Minimalist", "Casual", "Streetwear", "Smart casual", "Formal", "Vintage", "Sporty", "Preppy", "Bohemian"]
PATTERNS = ["Solid", "Stripes", "Checks", "Floral", "Graphic", "Animal print", "Other"]
OCCASIONS = ["Casual", "School", "Party", "Dinner", "Formal event"]

with st.sidebar:
    st.header("Navigate")
    page = st.radio("Choose a page", ["My Wardrobe", "Create outfit", "Saved outfits", "How it works"])
    st.divider()
    st.metric("Items in wardrobe", len(st.session_state.wardrobe))
    st.caption("This starter version stores data for the current Streamlit session. Refreshing or restarting may clear it.")

if page == "My Wardrobe":
    st.header("My Wardrobe")
    st.write("Add details about each item. More accurate descriptions help the recommender make better choices.")

    with st.form("add_clothing", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Item name", placeholder="e.g. White linen shirt")
            category = st.selectbox("Category", CATEGORIES)
            colour = st.selectbox("Main colour", COLOURS)
            style = st.selectbox("Style", STYLES)
        with col2:
            formality = st.slider("Formality", min_value=1, max_value=5, value=3,
                                  help="1 = very casual, 5 = very formal")
            pattern = st.selectbox("Pattern", PATTERNS)
            notes = st.text_input("Optional notes", placeholder="e.g. lightweight, oversized")
        submitted = st.form_submit_button("Add to wardrobe", type="primary")
        if submitted:
            if not name.strip():
                st.error("Please enter an item name.")
            else:
                st.session_state.wardrobe.append({
                    "id": len(st.session_state.wardrobe) + 1,
                    "name": name.strip(),
                    "category": category,
                    "colour": colour,
                    "style": style,
                    "formality": int(formality),
                    "pattern": pattern,
                    "notes": notes.strip()
                })
                st.success(f"Added {name.strip()} to your wardrobe.")

    st.subheader("Your items")
    if not st.session_state.wardrobe:
        st.info("Your wardrobe is empty. Add a few items above to get started. For a complete outfit, try adding a top, bottom and shoes — or a dress and shoes.")
    else:
        for item in st.session_state.wardrobe:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{item['name']}** · {item['category']}")
                    st.caption(f"{item['colour']} · {item['style']} · Formality {item['formality']}/5 · {item['pattern']}")
                    if item.get("notes"):
                        st.write(item["notes"])
                with col2:
                    if st.button("Remove", key=f"remove_{item['id']}"):
                        st.session_state.wardrobe = [x for x in st.session_state.wardrobe if x["id"] != item["id"]]
                        st.rerun()

elif page == "Create outfit":
    st.header("Create an outfit")
    st.write("Choose an occasion and your preferred style. Closet AI will create possible combinations and rank them.")

    col1, col2 = st.columns(2)
    with col1:
        occasion = st.selectbox("Occasion", OCCASIONS)
    with col2:
        preferred_style = st.selectbox("Style preference", ["Any"] + STYLES)

    st.caption("The scores are estimates based on transparent rules, not objective fashion judgments.")
    if st.button("Find my best outfits", type="primary", use_container_width=True):
        if len(st.session_state.wardrobe) < 2:
            st.warning("Add more wardrobe items first.")
        else:
            results = generate_ranked_outfits(
                st.session_state.wardrobe,
                occasion=occasion,
                preferred_style=preferred_style,
                ratings=st.session_state.ratings,
                limit=3
            )
            st.session_state.latest_results = results
            st.session_state.latest_occasion = occasion

    results = st.session_state.get("latest_results", [])
    if results:
        st.subheader(f"Top recommendations for {st.session_state.get('latest_occasion', 'your occasion')}")
        if not results:
            st.info("I couldn't make a complete outfit from those items. Add a top, bottom and shoes, or a dress and shoes.")
        for rank, result in enumerate(results, start=1):
            outfit = result["items"]
            names = " + ".join(x["name"] for x in outfit)
            with st.container(border=True):
                st.markdown(f"### #{rank} · {result['score']}/100")
                st.markdown(" · ".join(f"**{x['category']}:** {x['name']} ({x['colour']})" for x in outfit))
                st.progress(result["score"] / 100)
                st.write(result["explanation"])
                st.caption(
                    f"Colour: {result['breakdown']['colour']}/100 · "
                    f"Occasion: {result['breakdown']['occasion']}/100 · "
                    f"Style: {result['breakdown']['style']}/100 · "
                    f"Preference: {result['breakdown']['preference']}/100"
                )
                feedback_key = f"rating_{result['key']}"
                current_rating = st.session_state.ratings.get(result["key"], 0)
                chosen_rating = st.select_slider(
                    "How much do you like this outfit?",
                    options=[0, 1, 2, 3, 4, 5],
                    value=current_rating,
                    format_func=lambda x: "Not rated" if x == 0 else f"{x}/5 ★",
                    key=feedback_key
                )
                c1, c2 = st.columns([1, 4])
                with c1:
                    if st.button("Save outfit", key=f"save_{result['key']}"):
                        if not any(x["key"] == result["key"] for x in st.session_state.saved_outfits):
                            st.session_state.saved_outfits.append({
                                "key": result["key"],
                                "occasion": st.session_state.get("latest_occasion", occasion),
                                "items": outfit,
                                "score": result["score"],
                                "explanation": result["explanation"]
                            })
                        st.success("Outfit saved.")
                with c2:
                    if chosen_rating:
                        st.session_state.ratings[result["key"]] = chosen_rating
                    elif result["key"] in st.session_state.ratings:
                        del st.session_state.ratings[result["key"]]
        st.caption("Rate outfits to influence future rankings. Ratings are stored only for this session in this starter version.")

elif page == "Saved outfits":
    st.header("Saved outfits")
    if not st.session_state.saved_outfits:
        st.info("No saved outfits yet. Go to Create outfit and save a recommendation.")
    else:
        for idx, outfit in enumerate(st.session_state.saved_outfits, start=1):
            with st.container(border=True):
                st.markdown(f"### Saved outfit {idx} · {outfit['score']}/100")
                st.caption(f"Occasion: {outfit['occasion']}")
                st.write(" · ".join(f"{x['name']} ({x['colour']})" for x in outfit["items"]))
                st.write(outfit["explanation"])
                if st.button("Remove saved outfit", key=f"delete_saved_{outfit['key']}"):
                    st.session_state.saved_outfits = [x for x in st.session_state.saved_outfits if x["key"] != outfit["key"]]
                    st.rerun()

else:
    st.header("How Closet AI works")
    st.markdown("""
    **1. Generate:** The app creates combinations from the items you enter. It supports a top + bottom + shoes outfit, a dress + shoes outfit, and optional outerwear/accessories.

    **2. Score:** Each combination gets a score out of 100 based on:
    - **Colour coordination (35%)** — simple colour-palette rules, such as neutrals, monochrome and compatible colour families.
    - **Occasion suitability (30%)** — how close the clothing formality levels are to the occasion's target.
    - **Style consistency (20%)** — whether the styles are compatible.
    - **Personal preference (15%)** — your previous ratings, where available.

    **3. Rank:** The app shows the three highest-ranked combinations with a short explanation.

    **4. Learn from feedback:** Rate recommendations from 1–5 stars. Higher-rated outfits can improve the preference component of later recommendations.

    **Important:** This version uses a rule-based recommendation algorithm, not a trained machine-learning model or image-recognition model. That makes it easier to inspect and test. A later version could add photo uploads, computer vision, persistent storage and a model trained on ratings.
    """)

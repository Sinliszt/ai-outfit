import streamlit as st
from recommender import generate_outfit

st.set_page_config(
    page_title = "AI Outfit Generator"
)

st.title("AI Outfit Generator")

page = st.sidebar.selectbox(
    "Navigate",
    ["My Wardrobe", "Create outfit", "Saved outfits"]
)

if page == "My Wardrobe":
    st.header("My Wardrobe")
    st.write("Add and manage closet pieces")

    st.subheader("Add a clothing item")

    with st.form("clothing_form"):
        name = st.text_input("Item name")

        category = st.selectbox(
            "Category",
            ["Top", "Bottom", "Dress", "Shoes", "Outerwear", "Accessory"]
        )

        colour = st.selectbox(
            "Main colour",
            ["Black", "White", "Grey", "Beige", "Brown", "Blue", "Red", "Green", "Pink", "Other"]
        )

        style = st.selectbox(
            "Style",
            ["Casual", "Minimalist", "Streetwear", "Formal", "Vintage", "Sporty"]
        )

        submitted = st.form_submit_button("Add item")

        if submitted:
            if name.strip():
                item = {
                    "name": name.strip(),
                    "category": category,
                    "colour": colour,
                    "style": style

                }

                st.session_state.wardrope.append(item)
                st.success(f"{name} added to your wardrobe!")
            else:
                st.warning("Please enter something")

        st.divider()
        st.subheader("Your clothing items")

        if st.session_state.wardrobe:
            for index, item in enumerate(st.session_state.wardrobe):
                with st.container(border = True):
                    st.write(f"**{item['name']}")
                    st.write(f"Category: {item['category']}")
                    st.write(f"Colour: {item['colour']}")
                    st.write(f"Style: {item['style']}")

                    if st.button("Remove item", key=f"remove_{index}"):
                        st.sesion_state.wardrobe.pop(index)
                        st.rerun()

        else:
            st.info("Your wardrobe is empty")

elif page == "Create outfit":
    st.header("Outfit Creator")
    st.write("Generate an outfit using clothes you already own.")

    occasion = st.selectbox(
        "What is the occasion?",
        ["Casual", "School", "Party", "Dinner", "Formal event"]
    )

    if st.button("Generate outfit"):
        if not st.session_state.wardrobe:
            st.warning("Add some clothes to your wardrobe first.")
        else:
            outfit = generate_outfit(
                st.session_state.wardrobe,
                occasion
            )
            if outfit is None:
                st.warning(
                    "You don't have enough compatible categories "
                    "to generate a complete outfit. Add more clothes!"
                )
            else:
                st.subheader("Your recommended outfit")
                for item in outfit:
                    st.write(
                        f"**{item['category']}:** {item['name']} "
                        f"({item['colour']}, {item['style']})"
                    )
elif page == "Saved outfits":
    st.header("Saved outfits")
    st.write("See outfits that you've already made")
# Bank Customer Churn Dashboard

An interactive Streamlit dashboard for exploring customer churn by country, gender, age, tenure, activity, and account balance.

## Run locally

```bash
py -m pip install -r requirements.txt
py -m streamlit run app.py
```

The app starts with generated demo data. Use the sidebar to upload a CSV containing these columns:

`CustomerId`, `Surname`, `CreditScore`, `Geography`, `Gender`, `Age`, `Tenure`, `Balance`, `NumOfProducts`, `HasCrCard`, `IsActiveMember`, `EstimatedSalary`, `Exited`

## Deploy with Streamlit Community Cloud

1. Create a new public GitHub repository.
2. Upload `app.py`, `requirements.txt`, `readme.md`, and `.gitignore` to the repository root.
3. Open [share.streamlit.io](https://share.streamlit.io/) and sign in with GitHub.
4. Select **New app**, choose your repository and branch, and set the main file to `app.py`.
5. Select **Deploy**. Streamlit Cloud installs the packages from `requirements.txt` automatically.

After deployment, commit and push future changes to GitHub. Streamlit Cloud will rebuild the app automatically.

from flask import Flask, render_template, request, send_file
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import pandas as pd
import os

app = Flask(__name__)
loop = asyncio.get_event_loop()


async def scrape_data(zipcode):
    data = {
        "Name": [],
        "Address": [],
        "Contact Person": [],
        "Overdue": [],
        "Url Link": [],
    }

    async with aiohttp.ClientSession() as session:
        for pageNo in range(1, 21):
            url = f"https://find-and-update.company-information.service.gov.uk/search/companies?q={zipcode}&page={pageNo}"
            async with session.get(url) as response:
                if response.status == 200:
                    soup = BeautifulSoup(await response.text(), "html.parser")
                    try:
                        allcompanieslink = (
                            soup.find("div", id="search-container")
                            .find("div", class_="column-full-width")
                            .find("div", class_="grid-row")
                            .find("div", class_="column-two-thirds")
                            .find("article", id="services-information-results")
                            .find("ul", id="results")
                            .find_all("li")
                        )
                        for company in allcompanieslink:
                            companylink = company.find("a")["href"]
                            dissolved = (
                                company.find("p").get_text().__contains__("Dissolved")
                            )
                            registered = (
                                company.find("p").get_text().__contains__("Registered")
                            )
                            if not dissolved:  # skip dissolved accounts
                                companyName = (
                                    company.find("a")
                                    .get_text()
                                    .replace("         ", " ")
                                    .replace("\n", " ")
                                    .replace("      ", " ")
                                )
                                companylink = (
                                    "https://find-and-update.company-information.service.gov.uk"
                                    + companylink
                                )
                                async with session.get(companylink) as resultResponse:
                                    if resultResponse.status == 200:
                                        resultList = BeautifulSoup(
                                            await resultResponse.text(), "html.parser"
                                        )
                                        itemlist = (
                                            resultList.find(
                                                "div", id="content-container"
                                            )
                                            .find("div", class_="govuk-tabs")
                                            .find("ul", class_="govuk-tabs__list")
                                            .find_all("li")
                                        )
                                        companyoverView = (
                                            "https://find-and-update.company-information.service.gov.uk"
                                            + itemlist[0].find("a")["href"]
                                        )
                                        try:
                                            if len(itemlist) >= 2:
                                                companyPeople = (
                                                    "https://find-and-update.company-information.service.gov.uk"
                                                    + itemlist[2].find("a")["href"]
                                                )
                                        except IndexError:
                                            continue

                                        async with session.get(
                                            companyoverView
                                        ) as companyResponse:
                                            if companyResponse.status == 200:
                                                company_soup = BeautifulSoup(
                                                    await companyResponse.text(),
                                                    "html.parser",
                                                )
                                                tabList = (
                                                    company_soup.find(
                                                        "div", id="content-container"
                                                    )
                                                    .find("div", class_="govuk-tabs")
                                                    .find(
                                                        "ul", class_="govuk-tabs__list"
                                                    )
                                                    .find_all("li")
                                                )
                                                detailsBox = company_soup.find(
                                                    "div", class_="govuk-tabs__panel"
                                                )
                                                officeAddress = (
                                                    detailsBox.find("dd")
                                                    .get_text()
                                                    .replace("\n", " ")
                                                )
                                                AccountOverview = (
                                                    "https://find-and-update.company-information.service.gov.uk"
                                                    + tabList[0].find("a")["href"]
                                                )

                                                async with session.get(
                                                    AccountOverview
                                                ) as result:
                                                    if result.status == 200:
                                                        soup = BeautifulSoup(
                                                            await result.text(),
                                                            "html.parser",
                                                        )
                                                        if not registered:
                                                            AccountStatus = (
                                                                soup.find(
                                                                    "div",
                                                                    id="content-container",
                                                                )
                                                                .find(
                                                                    "div",
                                                                    class_="govuk-tabs",
                                                                )
                                                                .find(
                                                                    "div",
                                                                    class_="govuk-tabs__panel",
                                                                )
                                                                .find_all(
                                                                    "div",
                                                                    class_="grid-row",
                                                                )
                                                            )
                                                            try:
                                                                AccountOverdue = (
                                                                    AccountStatus[2]
                                                                    .find(
                                                                        "div",
                                                                        class_="column-half",
                                                                    )
                                                                    .find("h2")
                                                                    .get_text()
                                                                )
                                                            except IndexError:
                                                                continue
                                                        else:
                                                            AccountStatus = (
                                                                soup.find(
                                                                    "div",
                                                                    id="content-container",
                                                                )
                                                                .find(
                                                                    "div",
                                                                    class_="govuk-tabs",
                                                                )
                                                                .find(
                                                                    "div",
                                                                    class_="govuk-tabs__panel",
                                                                )
                                                                .find_all(
                                                                    "div",
                                                                    class_="grid-row",
                                                                )
                                                            )
                                                            AccountOverdue = (
                                                                AccountStatus[2]
                                                                .find("h2")
                                                                .get_text()
                                                            )
                                                        if (
                                                            "overdue" in AccountOverdue
                                                        ):  # Only overdue Accounts details will be saved
                                                            AccountDate = (
                                                                AccountStatus[2]
                                                                .find(
                                                                    "div",
                                                                    class_="column-half",
                                                                )
                                                                .find("p")
                                                                .get_text()
                                                            )
                                                            AccountDate = (
                                                                AccountDate.replace(
                                                                    "         ", " "
                                                                )
                                                                .replace("\n", " ")
                                                                .replace("      ", " ")
                                                            )
                                                            if (
                                                                "2022" in AccountDate
                                                                or "2023" in AccountDate
                                                            ):  # only 2022/2023 records
                                                                async with session.get(
                                                                    companyPeople
                                                                ) as response:
                                                                    if (
                                                                        response.status
                                                                        == 200
                                                                    ):
                                                                        companyContact_soup = BeautifulSoup(
                                                                            await response.text(),
                                                                            "html.parser",
                                                                        )
                                                                        cp = ""
                                                                        detailsBox = companyContact_soup.find(
                                                                            "div",
                                                                            class_="govuk-tabs__panel",
                                                                        )
                                                                        outerDiv = companyContact_soup.find(
                                                                            "div",
                                                                            class_="appointments-list",
                                                                        )
                                                                        companyContactPerson = outerDiv.find_all(
                                                                            "div"
                                                                        )
                                                                        for (
                                                                            person
                                                                        ) in companyContactPerson:
                                                                            if (
                                                                                person.find(
                                                                                    "a"
                                                                                )
                                                                                is not None
                                                                            ):
                                                                                if (
                                                                                    person.find(
                                                                                        "div",
                                                                                        class_="grid-row",
                                                                                    )
                                                                                    .find(
                                                                                        "span"
                                                                                    )
                                                                                    .get_text()
                                                                                    == "Active"
                                                                                ):
                                                                                    cp += (
                                                                                        person.find(
                                                                                            "a"
                                                                                        ).get_text()
                                                                                        + " "
                                                                                    )
                                                                        contactperson = (
                                                                            cp
                                                                        )
                                                                        data[
                                                                            "Overdue"
                                                                        ].append(
                                                                            AccountDate
                                                                        )
                                                                        data[
                                                                            "Name"
                                                                        ].append(
                                                                            companyName
                                                                        )
                                                                        data[
                                                                            "Address"
                                                                        ].append(
                                                                            officeAddress
                                                                        )
                                                                        data[
                                                                            "Url Link"
                                                                        ].append(
                                                                            companylink
                                                                        )
                                                                        data[
                                                                            "Contact Person"
                                                                        ].append(
                                                                            contactperson
                                                                        )
                    except AttributeError:
                        print("")
    return data


def get_overdue_accounts(data):
    overdue_accounts = []
    for i in range(len(data["Name"])):
        account = {
            "Name": data["Name"][i],
            "Address": data["Address"][i],
            "Contact Person": data["Contact Person"][i],
            "Overdue": data["Overdue"][i],
            "Url Link": data["Url Link"][i],
        }
        overdue_accounts.append(account)

    return overdue_accounts


@app.route("/download", methods=["POST"])
def download():
    zipcode = request.form["zipcode"]
    filename = f"{zipcode}.xlsx"
    if os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return "File Not Found."


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        zipcode = request.form["zipcode"]
        if not zipcode:
            return "Please enter a valid postcode."

        # Perform web scraping
        data = loop.run_until_complete(scrape_data(zipcode))

        if data["Overdue"]:
            filename = f"{zipcode}.xlsx"
            df = pd.DataFrame.from_dict(data)
            df.to_excel(filename, index=False)
            overdue_accounts = get_overdue_accounts(
                data
            )  # Get overdue accounts details
            return render_template("index.html", overdue_accounts=overdue_accounts)
        else:
            return render_template("index.html")

    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')

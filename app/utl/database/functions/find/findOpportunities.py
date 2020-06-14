from copy import deepcopy

from sqlalchemy import and_, or_

from utl.database.models.models import (
    db,
    Opportunity,
    OpportunityGrade,
    OpportunityLink,
)


def hasFilters(filters):
    """
    input:
    {field: ["ACADEMIC PROGRAMS", "ENGINEERING, MATH, & CS", "MEDICAL & LIFE SCIENCES"],
        maximum-cost: 500, grade: ["JUNIOR", "SENIOR"], gender: ["CO-ED", "FEMALE"]}
    output:
    True or False
    """
    return (
        len(filters["field"])
        or filters["maximum-cost"]
        or len(filters["grade"])
        or len(filters["gender"])
    )


def searchOpportunities(baseQuery, search):
    if search and search.strip():
        searchQueryString = "%" + search + "%"

        searchQuery = baseQuery.filter(
            or_(
                Opportunity.title.ilike(searchQueryString),
                Opportunity.description.ilike(searchQueryString),
            )
        )

        return searchQuery
    # At this point search is something like None or ""
    # Only baseQuery is returned because the original search space is not minimized in any way
    return baseQuery


def filterOpportunities(baseQuery, filtersDict):
    if not hasFilters(filtersDict):
        return baseQuery

    fieldFilters = filtersDict["field"]
    maximumCostFilter = filtersDict["maximum-cost"]
    gradeFilters = filtersDict["grade"]
    genderFilters = filtersDict["gender"]
    filters = []

    for key, val in filtersDict.items():
        orFilters = []
        if key == "field":
            for fieldFilter in val:
                orFilters.append(Opportunity.field == fieldFilter)
                filters.append(or_(*orFilters))
        elif key == "maximum-cost":
            for maximumCostFilter in val:
                orFilters.append(Opportunity.cost == maximumCostFilter)
                filters.append(or_(*orFilters))
        elif key == "grade":
            for gradeFilter in val:
                orFilters.append(Opportunity.grade == gradeFilter)
                filters.append(or_(*orFilters))
        elif key == "gender":
            for genderFilter in val:
                orFilters.append(Opportunity.gender == genderFilter)
                filters.append(or_(*orFilters))

    return baseQuery.filter(and_(*filters))


def sortOpportunities(baseQuery, sort):
    sortOptionQueries = {
        "cost-asc": Opportunity.cost.asc(),
        "cost-desc": Opportunity.cost.desc(),
        "deadline-asc": Opportunity.deadline.asc(),
        "deadline-desc": Opportunity.deadline.desc(),
        "dateposted-asc": Opportunity.datePosted.asc(),
        "dateposted-desc": Opportunity.datePosted.desc(),
    }

    # default sort option
    sortOptionQuery = "dateposted-asc"

    # Check if sort is a truey value (i.e. not None or "") and is a key in sortOptionQueries
    if sort and sort in sortOptionQueries.keys():
        sortOptionQuery = sort

    sortedOpportunitiesQuery = baseQuery.order_by(sortOptionQueries[sortOptionQuery])

    return sortedOpportunitiesQuery


def findOpportunities(body):
    """
    input:
    {
        filters: {field: ["ACADEMIC PROGRAMS", "ENGINEERING, MATH, & CS", "MEDICAL & LIFE SCIENCES"], maximum-cost: 500, grade: ["JUNIOR", "SENIOR"], gender: ["CO-ED", "FEMALE"]},
        search: "query",
        sort: "sort-order"
    }
    output:
    body (provided input), array of opportunity objects
    """
    filters = body["filters"]
    search = body["search"]
    sort = body["sort"]
    baseQuery = Opportunity.query

    # Evaluate query generated by fxn compositions
    sortedOpportunities = sortOpportunities(
        filterOpportunities(searchOpportunities(baseQuery, search), filters), sort,
    ).all()

    # Attaching grades and links to the list of sorted Opportunity objects
    for opportunity in sortedOpportunities:
        grades = OpportunityGrade.query.filter_by(
            opportunityID=opportunity.opportunityID
        ).all()
        opportunity.grades = [grade.grade for grade in grades]
        links = OpportunityLink.query.filter_by(
            opportunityID=opportunity.opportunityID
        ).all()
        opportunity.links = [link.link for link in links]

    return (body, sortedOpportunities)

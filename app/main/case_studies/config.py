from datetime import date

study_config = {
    # slug (url route) => data
    # If date is in the future, only sudo can see it on list page
    "on-demand-startup": {
        # Actual title of case study
        "name":
        "Staffjoy Decreases Labor Costs 10% at On-Demand Startup",
        # Short, less editorial name for use on the case studies list page
        "short_name":
        "On-Demand Startup",
        "hero_image":
        "/static/images/case-studies/on-demand-startup.jpg",
        "summary":
        "Staffjoy scheduling technology decreased labor costs 10% at a major on-demand startup. This case study looks at how and why optimal scheduling saved so much money.",
        "source":
        "on-demand-startup.md",
        "publication":
        date(2015, 8, 30),
        "public":
        False,  # Has this been published?
        "header_inject":
        '<script type="text/javascript" src="/static/javascript/case-studies/on-demand-startup.js"></script><!-- Thanks to Unsplash.com for the image https://images.unsplash.com/23/parked-bike.JPG?q=80&fm=jpg&s=421fbe84e82d18750091a19109d3e87e -->',
    },
}

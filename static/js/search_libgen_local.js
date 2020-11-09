
function displayResults(results) {
    const cols = ["Author(s)", "Title", "Year", "Language", "Available", "Download"];

    const table = document.getElementById("results");
    table.innerHTML = "";
    const header = document.createElement("tr");
    header.setAttribute("class", "header");
    for (const col of cols) {
        const colHeader = document.createElement("th");
        colHeader.appendChild(document.createTextNode(col));
        header.appendChild(colHeader);
    }
    table.appendChild(header);

    for (const i of results) {
        const row = document.createElement("tr");
        const rowData = calculateRow(i);
        for (const col of cols) {
            const datum = rowData[col];
            const tdClass = "data-" + col;
            let cell;
            if (typeof datum == "string") {
                cell = document.createElement("td");
                cell.appendChild(document.createTextNode(datum));
            } else if (typeof datum == "object" && (datum instanceof HTMLElement)) {
                if (datum.nodeName == "td") {
                    cell = datum;
                } else {
                    cell = document.createElement("td");
                    cell.appendChild(datum);
                }
            } else {
                cell = document.createElement("td");
                cell.appendChild(document.createTextNode("calculation error"));
            }
            cell.classList.add("data-" + col.toLowerCase());
            row.appendChild(cell);
        }
        table.appendChild(row);
    }
}

function calculateRow(i) {
    const links_href = calculateLinks(i);
    const links_td = document.createElement("td");
    for (let i=0; i<links_href.length; i++) {
        const link_a = document.createElement("a");
        link_a.setAttribute("target", "_blank");
        link_a.setAttribute("href", links_href[i]);
        link_a.appendChild(document.createTextNode("[" + (i+1) + "]"));
        links_td.appendChild(link_a);
    }

    const title_td = document.createElement("td");
    if (getData("series", i)) {
        const series_span = document.createElement("span");
        series_span.appendChild(document.createTextNode(getData("series", i))); // TODO: search by series link
        series_span.setAttribute("class", "data-series");
        title_td.appendChild(series_span);
        title_td.appendChild(document.createElement("br"));
    }
    const title_span = document.createElement("span");
    title_span.appendChild(document.createTextNode(getData("title", i)));
    title_td.appendChild(title_span);

    return {
        "Id": getData("collection", i) + ":" + getData("id", i),
        "Author(s)": getData("author", i), // TODO: search by author
        "Title": title_td,
        "Year": getData("year", i) == "0" ? "" : getData("year", i),
        "Language": getData("language", i).replace(/,([^ ])/g, ', $1'),
        "Available": getData("text_available", i),
        "Download": links_td,
    };
}

function humanReadableBytes(bytes) {
    if (bytes < 1000) {
        return bytes + "B";
    }
    const kb = Math.round(bytes / 1000);
    if (kb < 1000) {
        return kb + "KB";
    }
    const mb = Math.round(kb / 1000);
    if (mb < 1000) {
        return mb + "MB";
    }
    const gb = Math.round(mb / 1000);
    return gb + "GB";
}

function calculateLinks(i) {
    const ff = (getData("collection", i) == "ff");
    const lg = (getData("collection", i) == "lg");
    const md5 = getData("md5", i).toLowerCase();
    const id = getData("id", i);
    const extension = getData("extension", i);
    const group = (Math.floor(parseInt(id)/1000)*1000).toString();
    const available = getData("text_available", i) === "yes";

    if (!available) return [];
    if (ff) {
        return [
            `../book/ff/${group}/${md5}.txt`
        ];
    } else if (lg) {
        return [
            `../book/lg/${group}/${md5}.${extension}.txt`
        ];
    }
    return [];
}

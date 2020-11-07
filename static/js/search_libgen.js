
function displayResults(results) {
    const cols = ["Author(s)", "Title", "Year", "Language", "File", "Download"];

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
        const rowData = calculateRow(corpus.data, i);
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

function calculateRow(data, i) {
    const links_href = calculateLinks(data, i);
    const links_td = document.createElement("td");
    for (let i=0; i<links_href.length; i++) {
        const link_a = document.createElement("a");
        link_a.setAttribute("target", "_blank");
        link_a.setAttribute("href", links_href[i]);
        link_a.appendChild(document.createTextNode("[" + (i+1) + "]"));
        links_td.appendChild(link_a);
    }

    const title_td = document.createElement("td");
    if (data["series"][i]) {
        const series_span = document.createElement("span");
        series_span.appendChild(document.createTextNode(data["series"][i])); // TODO: search by series link
        series_span.setAttribute("class", "data-series");
        title_td.appendChild(series_span);
        title_td.appendChild(document.createElement("br"));
    }
    const title_span = document.createElement("span");
    title_span.appendChild(document.createTextNode(data["title"][i]));
    title_td.appendChild(title_span);

    return {
        "Id": data["collection"][i] + ":" + data["id"][i],
        "Author(s)": data["author"][i], // TODO: search by author
        "Title": title_td,
        "Year": data["year"][i] == "0" ? "" : data["year"][i],
        "Language": data["language"][i].replace(/,([^ ])/g, ', $1'),
        "File": data["extension"][i] + " / " + humanReadableBytes(data["filesize"][i]),
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

function calculateLinks(data, i) {
    const ff = (data["collection"][i] == "ff");
    const lg = (data["collection"][i] == "lg");
    const MD5 = data["md5"][i].toUpperCase();
    const md5 = data["md5"][i].toLowerCase();
    const id = data["id"][i];
    const filename = data["title"][i] + "." + data["extension"][i];

    let links = [];

    const torrent_group = data["torrent_group"][i];
    const torrent_file_num = data["torrent_file_num"][i];
    if (typeof(torrent_group) == 'number') {
        let torrent_filename = "";
        if (lg && torrent_group == 0) {
            torrent_filename = "r_000.torrent";
        } else if (lg) {
            torrent_filename = `r_${torrent_group*1000}.torrent`;
        } else {
            torrent_filename = `f_${torrent_group*1000}.torrent`;
        }
        
        const torrent_infohash = corpus.infohash[`${data["collection"][i][0]}${torrent_group}`];
        if (torrent_infohash) {
            links.push(['magnet', `magnet:?xt=urn:btih:${torrent_infohash}&so=${torrent_file_num}`]); // BEP 53 (select one file). works like normal magnet link if this fails in clients I tested
        }

        if (lg) {
            links.push(['web-torrent', `http://gen.lib.rus.ec/repository_torrent/${torrent_filename}`]);
            links.push(['web-torrent', `http://libgen.rs/repository_torrent/${torrent_filename}`]);
        } else if (ff) {
            links.push(['web-torrent', `http://libgen.rs/fiction/repository_torrent/${torrent_filename}`]);
            links.push(['web-torrent', `http://gen.lib.rus.ec/fiction/repository_torrent/${torrent_filename}`]);
        } 
    }

    const ipfs_cid = data["ipfs_cid"][i];
    if (ipfs_cid) {
        links.push(['ipfs-gateway', `https://ipfs.io/ipfs/${ipfs_cid}?filename=${filename}`]);
        links.push(['ipfs-gateway', `https://cloudflare-ipfs.com/ipfs/${ipfs_cid}?filename=${filename}`]);
        links.push(['ipfs-gateway', `https://ipfs.infura.io/ipfs/${ipfs_cid}?filename=${filename}`]);
        links.push(['ipfs', `ipfs://${ipfs_cid}`]);
    }

    if (ff) {
        links.push(['web', `http://library.lol/fiction/${MD5}`]);
        links.push(['web', `http://libgen.lc/foreignfiction/ads.php?md5=${MD5}`]);
        links.push(['web', `http://b-ok.cc/md5/${MD5}`]);
        links.push(['web', `http://fiction.libgen.me/item/detail/${md5}`]);
    } else if (lg) {
        links.push(['web', `http://library.lol/main/${MD5}`]);
        links.push(['web', `http://libgen.lc/ads.php?md5=${MD5}`]);
        links.push(['web', `http://b-ok.cc/md5/${MD5}`]);
        links.push(['web', `https://libgen.pw/item?id=${id}`]);
        links.push(['web', `http://bookfi.net/md5/${MD5}`]);
    }

    let ret = [];
    for (const type of ['ipfs-gateway', 'magnet', 'web']) {
        for (const l of links) {
            if (l[0] == type) ret.push(l[1]);
        }
    }
    return ret;
}

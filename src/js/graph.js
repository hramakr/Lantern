
// --------------------------------------------------------------------------------
// Graph
// Define a generic d3 graph object.
// --------------------------------------------------------------------------------

// This makes a generic graph object that encapsulates a d3 force layout object,
// and provides some access functions.

// Nodes can be any javascript object with 'key', 'name', and optional 'desc' properties.
// Links are just pairs of node keys.

// Usage:
// var graph = new Graph('#map', {charge: -5000, gravity: 0.5, distance: 90, nodeRadius: 20});
// var room = {key:'foo', name:'Foo', desc:'A dusty room'};
// graph.addNode(room);

// For reference, see
// http://bl.ocks.org/mbostock/3750558

// --------------------------------------------------------------------------------

// globals defined elsewhere - basically 'imported' by index.html
var d3; // index.html
var Hash, getWindowSize; // library.js


//> get rid of global 'onClickNode' reference


var Graph = function (parentElement, options={}) {

    // set graph options
    var charge = options.charge || -5000; // attractive/repulsive force
    var gravity = options.gravity || 0.5; // force drawing nodes to the center
    var distance = options.distance || 90; // fixed distance between nodes
    var nodeRadius = options.nodeRadius || 20; // pixels

    // set label positions
    var labelx = nodeRadius + 4; // pixels
    var labely = nodeRadius / 4; // pixels

    // arrays of nodes (rooms) and links
    var nodes, links;

    // need to store a hash of added objects, so can avoid duplicate rooms.
    // could just use a Set, but also need to be able to find the room objects.
    var nodeHash = new Hash();

    //> could store a set of link keys to avoid duplicate links also,
    // but we won't be duplicating them very often.
    // var linkkeys = new Set();

    // create svg canvas as child of parent element and return a d3 svg object
    var svg = d3.select(parentElement).append("svg");

    // add a rectangle filling the canvas
    //> get size of parent element, if possible
    var size = getWindowSize();
    size[1] -= 100; //> arbitrary
    svg.append("rect").attr("width", size[0]).attr("height", size[1]);

    // create a d3 force layout object and set some properties
    var force = d3.layout.force()
        .size(size)
        .distance(distance)
        .charge(charge)
        .gravity(gravity)
        .on("tick", tick);

    // update svg elements for current nodes and links,
    // and restart the d3 force layout object.
    function updateSvg() {

        // update links
        // links are just lines between nodes

        // select all svg line elements with class 'link'
        links = svg.selectAll("line.link")
            // assign a link key to each element, eg "whous-shous"
            .data(force.links(), function(d) { return d.source.key + "-" + d.target.key; });
            // .data(force.links());

        // add new link elements
        links.enter()
            .append("line")
            .attr("class", "link");

        // remove old elements
        links.exit()
            .remove();

        // force.start();

        // update nodes
        // nodes are svg group objects with circle and text children

        // select all svg group elements with class 'node'
        nodes = svg.selectAll("g.node")
            .data(force.nodes(), function(d) { return d.key;}); // assign a key to each element
            // .data(force.nodes()); // assign a key to each element

        // add new group elements
        nodes.enter()
            .append("g") // g is an svg group element
            .attr("class", "node"); // set class to 'node'

        // add some properties for the group element
        nodes.call(force.drag) // make nodes draggable
            .on("click", onClickNode) // callback fn to handle clicks
            .append("svg:title") // add a tooltip for each node showing the value of .desc
            .text(function(d) { return d.desc || "(No description)"; });

        // remove any old elements
        nodes.exit()
            .remove();

        // add circle elements to groups
        nodes.append("circle")
            .attr("r", nodeRadius);

        // add text elements to groups
        nodes.append("text")
            .attr("class", "nodetext")
            .attr("x", labelx)
            .attr("y", labely)
            .text(function(d) {return d.name;});


        // restart the d3 force layout object
        force.start();
    };

    // this function is called on each time tick to animate the graph.
    //> why is this needed if it's assigning fns to these attributes?
    // couldn't you just do that once?
    function tick() {
        nodes
            .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
            // .attr("cx", function(d) { return d.x; })
            // .attr("cy", function(d) { return d.y; });
        links
            .attr("x1", function(d) { return d.source.x; })
            .attr("y1", function(d) { return d.source.y; })
            .attr("x2", function(d) { return d.target.x; })
            .attr("y2", function(d) { return d.target.y; });
    };


    // return access functions
    return {

        // add a node to the graph, update the svg elements, and restart the layout.
        // a node can be any javascript object with a .key property.
        addNode: function (node) {
            if (node && !nodeHash.has(node.key)) {
                force.nodes().push(node);
                nodeHash.set(node.key, node);
                updateSvg();
            }
        },

        // add a link to the graph, update the svg elements, and restart the layout.
        // a link is just a pair of node keys.
        // dir is a direction - not used yet.
        addLink: function (sourceKey, targetKey, dir) {
            //> don't add if already there
            // var linkKey = sourceKey + '-' + targetKey;
            // if (! linkKeys.has(linkKey)) {
                // linkKeys.add(linkKey) etc
            var sourceNode = nodeHash.get(sourceKey);
            var targetNode = nodeHash.get(targetKey);
            if (sourceNode && targetNode) {
                // d3 expects links to have 'source' and 'target' properties linking
                // to the full node objects. dir is extra.
                var link = {"source": sourceNode, "target": targetNode, "dir": dir};
                force.links().push(link);
                updateSvg();
            }
        }
    };
};


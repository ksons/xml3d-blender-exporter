var d3 = require('d3')
 , pretty = require('prettysize');


module.exports = function(root) {
        var palette = {
            "scene": "#EAD177",
            "assets": "#D95B45",
            "materials": "#C12940"
        }

        var width = 500, height = 500, radius = Math.min(width, height) * 0.45;// color = d3.scale.category20c();
        var color = function(d) {
            if (d in palette) {
                return palette[d];
            }
            console.log("color", d);
            return "#efefef";
        }

 var svg = d3.select(".d3Target").append("svg").attr("width", width).attr("height", height).append("g").attr("transform", "translate(" + width /2 + "," + height /2 + ")");

    var partition = d3.layout.partition()
                            .sort(null)
                            .size([2 * Math.PI, radius * radius])
                            .value(function (d) {
                                return d.size;
                        });

        var groups = svg.datum(root).selectAll('g')
      .data(partition.nodes)
    .enter()
      .append('g');




         var title = svg.append('text')
            .text(root.name)
            .attr('x', 0)
            .attr('y', -5)
            .style('font-size', '12px')
            .style('fill', 'black')
            .style('font-weight', 500)
            .style('alignment-baseline', 'middle')
            .style('text-anchor', 'middle');

              var size = svg.append('text')
    .text(pretty(root.size))
    .attr('x', 0)
    .attr('y', 15)
    .style('fill', 'black')
    .style('font-size', '10px')
    .style('alignment-baseline', 'middle')
    .style('text-anchor', 'middle');

        var arc = d3.svg.arc().startAngle(function (d) {
            return d.x;
        }).endAngle(function (d) {
            return d.x + d.dx;
        }).innerRadius(function (d) {
            return Math.sqrt(d.y);
        }).outerRadius(function (d) {
            return Math.sqrt(d.y + d.dy * 0.75);
        });

            var path = groups.append("path").attr("display", function (d) {
                return d.depth ? null : "none";
            }) // hide inner ring
                .attr("d", arc).style("stroke", "#000").style("fill", function (d) {
                    return color((d.children ? d : d.parent).name);
                }).style("fill-rule", "evenodd").style("stroke-width", "1").each(stash);

  groups.on('mouseover', function(d) {
    //highlight(d)
    title.text(d.name)
    size.text(pretty(d.size))
  }).on('mouseout', function(d) {
    //unhighlight(d)
    title.text(root.name)
    size.text(pretty(root.size))
  })
            d3.selectAll("input").on("change", function change() {
                var value = this.value === "count" ? function () {
                    return 1;
                } : function (d) {
                    return d.size;
                };

                path.data(partition.value(value).nodes).transition().duration(1500).attrTween("d", arcTween);
            });

        // Stash the old values for transition.
        function stash(d) {
            d.x0 = d.x;
            d.dx0 = d.dx;
        }

        // Interpolate the arcs in data space.
        function arcTween(a) {
            var i = d3.interpolate({x: a.x0, dx: a.dx0}, a);
            return function (t) {
                var b = i(t);
                a.x0 = b.x;
                a.dx0 = b.dx;
                return arc(b);
            };
        }

        d3.select(self.frameElement).style("height", height + "px");
    };

<!DOCTYPE html>
<html>
    <head>
        <title></title>
        <style type="text/css">
         .q0-11{fill:rgb(38,0,165)}
         .q1-11{fill:rgb(215,48,39)}
         .q2-11{fill:rgb(244,109,67)}
         .q3-11{fill:rgb(253,174,97)}
         .q4-11{fill:rgb(254,224,139)}
         .q5-11{fill:rgb(255,255,191)}
         .q6-11{fill:rgb(217,239,139)}
         .q7-11{fill:rgb(166,217,106)}
         .q8-11{fill:rgb(102,189,99)}
         .q9-11{fill:rgb(26,152,80)}
         .q10-11{fill:rgb(104,155,0)}
        </style>
        <!-- Latest compiled and minified CSS -->
        <link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap.min.css">

        <!-- Optional theme -->
        <link rel="stylesheet" href="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/css/bootstrap-theme.min.css">

        <!-- Latest compiled and minified JavaScript -->
        <script src="http://code.jquery.com/jquery-1.10.1.min.js"></script>
        <script src="http://code.jquery.com/jquery-migrate-1.2.1.min.js"></script>
        <script src="http://netdna.bootstrapcdn.com/bootstrap/3.0.2/js/bootstrap.min.js"></script>
        <script src="http://d3js.org/d3.v3.min.js" charset="utf-8"></script>
    </head>
    <body>
        <div class="container">
        <div id="topics"></div>
        <table class="table" id="topic-data">
            %for row in xrange(som_height):
            <tr style="height: 40px;overflow:scroll;">
                %for col in xrange(som_width):
                    <td>
                        %if len(data[row][col])>0:
                            <a href="/unit/{{row}}/{{col}}" onmouseover="preview(this)" id="c{{row}}_{{col}}" class="somcell">{{len(data[row][col])}}</a>
                        %end
                        %#{{"%d %d" % (row, col)}}
                    </td>
                %end
            </tr>
            %end
        </table>
        </div>
        
        <script type="text/javascript">
            function preview(obj){
                obj.rel="[tooltip]"
                console.log($(obj))
                $.get(obj.href, {
                }, function(data) {
                    obj.title = data.keyword.join("\n")
                    $(obj).tooltip({placement:'right'})
                });
            }
            
            function pair(){
                s = this.id;
                a = s.split("_")
                return [parseInt(a[0].substr(1)), parseInt(a[1])];
            }
            function numtopic(){
                return parseInt(this.textContent);
            }
            
            var container = d3.select("#topics").append("svg").attr("width", 400).attr("height", 400)
            tmp = d3.select("#topic-data").selectAll(".somcell")
            
            var coords = tmp.datum(pair).data()
            var values = tmp.datum(numtopic).data()
            
            var color = d3.scale.quantize()
                                .domain([d3.min(values), d3.max(values)])
                                .range(d3.range(11).map(function(d){ return "q"+d+"-11";}))
            container.append("rect")
                .attr("x", 0)
                .attr("y",0)
                .attr("width", 400)
                .attr("height", 400)
                .style("fill","black")
            for(var i=0; i<coords.length; ++i){
                pt = coords[i]
                y = pt[0]
                x = pt[1]
                var circle = container.append("circle")
                circle.attr("cx", x * 10+5)
                circle.attr("cy", y * 10+5)
                circle.attr("r", 4)
                circle.attr("class", function(d) { return color(values[i]); })
            }
            d3.selectAll("circle").data(values)
        </script>
    </body>
</html>
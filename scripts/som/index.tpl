<!DOCTYPE html>
<html>
    <head>
        <title></title>
        <style type="text/css">
         .d3-tooltip{
            position: absolute;
            z-index: 10;
            visibility: hidden;
            padding: 2px;
            color:white;
            border-style: solid;
            border-color: "silver";
            border-radius: 4px;
            border-width: 1px;
            background-color: black;
            max-width: 450px;
            float: left;
         }
         
         #years{
            height: 600px;
            overflow:auto;
            overflow-x:hidden;
         }
         #authors{
            height: 600px;
            overflow-x:hidden;
            overflow-y:auto;
         }
        
        /* CSS3 scrollbar styling */        
         ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.3); 
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            border-radius: 10px;
            -webkit-box-shadow: inset 0 0 6px rgba(0,0,0,0.5); 
        }
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
            <div id="topics" class="col-md-7"></div>
            <div id="years" class="col-md-2"><h4>Year</h4></div>
            <div id="authors" class="col-md-3"><h4>Authors</h4></div>
        </div>
        
        <script type="text/javascript">
            var cells, dmin, dmax;
            
            d3.json("/unitdata.json", function(data){
                cells = data.result
                values = cells.map(function(d){return d.num})
                dmin = d3.min(values)
                dmax = Math.round(d3.max(values)/3)
                update(cells)
            })
            
            var container = d3.select("#topics").append("svg").attr("width", 600).attr("height", 600)
            
            //prepare tooltip
            var tooltip = d3.select("body")
                .append("div")
                .attr("class", "d3-tooltip")
                .text("a simple tooltip");
                
                
            //draw background
            container.append("rect")
                .attr("x", 0)
                .attr("y",0)
                .attr("width", 600)
                .attr("height", 600)
                .style("fill","black")
            
            function c(x){
                //return Math.round((x-dmin)/dmax)*(dmax-dmin);
                return 190-Math.round((x-dmin)/dmax*(190));
            }
            
            function update_cells(el, x, y)
            {
                d3.json("/unit/"+y+"/"+x, function(data){
                    el.attr("rel", "[tooltip]")
                    el.attr("title", data.keyword.join(", "))
                })
            }
                
            function update(dataset)
            {
                var circles = container.selectAll("circle").data(dataset).enter() .append("circle")
                    .attr("cx", function(d){return d.x*15+8;}).attr("cy", function(d){return d.y*15+8;})
                    //.attr("x", function(d){return d.x*14+2;}).attr("y", function(d){return d.y*14+2;})
                    .attr("r", 6)
                    .attr("id", function(d){ return "_unit_"+d.y+"_"+d.x})
                    //.attr("width", 12).attr("height", 12)
                    //.style("fill", function(d){return "rgb(160,"+c(d.num)+",50)";})
                    .style("fill", function(d){return "hsl("+c(d.num)+",50%,50%)";})
                    //.style("fill", "teal")
                    .on("mouseover", function(){
                        //console.log(this)
                        var el = d3.select(this)
                        e = el[0]
                        //console.log(this)
                        var title = $(this).attr("title")
                        if (title==undefined){
                            d = el.data()[0]
                            d3.json("/unit/"+d.y+"/"+d.x, function(data){
                                content = data.keyword.join(", ")
                                el.attr("rel", "[tooltip]")
                                el.attr("title", content)
                                tooltip.text(data.keyword.join(", "))
                                tooltip.style("visibility", "visible");
                            })
                        }
                        else{
                            tooltip.text(title)
                            tooltip.style("visibility", "visible");
                        }
                        //console.log(el)
                        //console.log(el.data()[0].v)
                    })
                    .on("mousemove", function(){return tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px");})
                    .on("mouseout", function(){return tooltip.style("visibility", "hidden");})
                    /*
                    var circles = container.selectAll("text")
                        .data(dataset)
                        .enter()
                        .append("text")
                        .text(function(d){return d.num})
                        .attr("x", function(d){return d.x*15+7-2*((d.num+"").length);})
                        .attr("y", function(d){return d.y*15+12;})
                        .style("stroke", "none")
                        .style("fill","white")
                        .style("font-size", "7pt")
                    */
            }
            
            var years;
            var rawyears;
            d3.json("/years.json", function(data){
                rawyears = data;
                years = data.results.bindings.map(function(d){ return {year: parseInt(d.year.value.substr(0, 4)), count:parseInt(d.yearlycount.value)} })
                d3.select("#years").selectAll("li")
                    .data(years)
                    .enter()
                    .append("li")
                    .text(function(d){ return d.year+" ("+d.count+")" })
                    .on("click", function(obj){
                        console.log(obj)//data point
                        console.log(this)//element (li)
                    })
            })
            
            var authors;
            d3.json("/authors.json", function(data){
                authors = data.results.bindings.map(function(d){ return {name: d.autor.value, count:parseInt(d.pubcount.value)} })
                d3.select("#authors").selectAll("li")
                    .data(authors)
                    .enter()
                    .append("li")
                    .text(function(d){ return d.name.substr(5).replace("_", ", ")+" ("+d.count+")" })
                    .on("click", function(obj){
                        console.log(obj)//data point
                        console.log(this)//element (li)
                    })
            })
            
            
                
        </script>
        <div style="height: 400px;">&nbsp;</div>
    </body>
</html>
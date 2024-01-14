function toggleForm() {
    var isAddExpenseClicked = false;
    var form = document.querySelector("form");
    var display = document.querySelectorAll("display")
    form.style.display = form.style.display === "none" ? "block" : "none";
    isAddExpenseClicked = !isAddExpenseClicked;
}


function showTotal(){
  var totalElement = document.getElementById("sum");
  var button = document.getElementById("sum-btn")

  if(totalElement.style.display==="none"){
    totalElement.style.display="block";
    button.innerText = "Hide Total";
  }
  else {
    totalElement.style.display = "none";
    button.innerText = "Show Total";
  }
}

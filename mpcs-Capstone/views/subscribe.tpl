%include('views/header.tpl')
<!-- Captures the user's credit card information and uses Javascript to send to Stripe -->

<div class="container">
        <div class="page-header">
                <h2>Subscribe</h2>
        </div>

        <p>You are subscribing to the GAS Premium plan. Please enter your credit card details to complete your subscription.</p><br />

        <form role="form" action="/subscribe" method="post" id="subscribe_form" name="subscribe_submit">
            Name on Credit Card: <input class="form-control input-lg required" type="text" size="20" data-stripe="name" /> <br />
            Credit Card Number: <input class="form-control input-lg required" type="text" size="20" data-stripe="number" /> <br />
            verification Code: <input class="form-control input-lg required" type="text" size="20" data-stripe="cvc" />  <br />
            Expiration Month: <input class="form-control input-lg required" type="text" size="20" data-stripe="exp-month" /> </br>
            Expiration Year: <input class="form-control input-lg required" type="text" size="20" data-stripe="exp-year" /> </br>
            <input id="bill-me" class="btn btn-lg btn-primary" type="submit" value="Subscribe" />
        </form>

</div> <!-- container -->

%rebase('views/base', title='GAS - Subscribe')

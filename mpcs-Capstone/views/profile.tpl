%include('views/header.tpl')

<div class="container">
    <div class="page-header">
        <h2>User Profile</h2>
    </div>
    <br />

    <ul>
    <div class="row">
        <b>Full Name: </b> {{auth.current_user.description}}  <br />
        <b>Username: </b> {{auth.current_user.username}} <br />
        <b>Subscription Level: </b> {{auth.current_user.role}} <br />
    </div>
    </ul> <hr />

    %if auth.current_user.role=='free_user':
        <a href="{{get_url('subscribe')}}">← Upgrade to Premium</a>
    %end

</div> <!-- container -->

%rebase('views/base', title='GAS - My Page')

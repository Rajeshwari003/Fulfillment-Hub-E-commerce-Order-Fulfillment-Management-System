from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fulfillment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)
db = SQLAlchemy(app)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    variant = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    warehouse = db.Column(db.String(40), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    location = db.Column(db.String(50), nullable=False)
    product = db.relationship('Product')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='Normal')
    status = db.Column(db.String(30), nullable=False, default='Received')
    deadline = db.Column(db.DateTime, nullable=False)
    courier = db.Column(db.String(60), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    box_id = db.Column(db.String(50))
    staging_location = db.Column(db.String(50))

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship('Order')
    product = db.relationship('Product')

class StockTransfer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    from_warehouse = db.Column(db.String(40), nullable=False)
    to_warehouse = db.Column(db.String(40), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(30), default='In Transit')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    product = db.relationship('Product')

class Shipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    courier = db.Column(db.String(60), nullable=False)
    pickup_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(30), default='Upcoming')
    order = db.relationship('Order')

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    issue_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default='Medium')
    status = db.Column(db.String(30), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    order = db.relationship('Order')

def iso(dt):
    return dt.isoformat() if dt else None

def product_json(p):
    return {'id': p.id, 'sku': p.sku, 'name': p.name, 'variant': p.variant, 'category': p.category, 'price': p.price}

def order_json(o):
    items = OrderItem.query.filter_by(order_id=o.id).all()
    return {
        'id': o.id, 'order_number': o.order_number, 'customer_name': o.customer_name,
        'priority': o.priority, 'status': o.status, 'deadline': iso(o.deadline),
        'courier': o.courier, 'created_at': iso(o.created_at), 'box_id': o.box_id,
        'staging_location': o.staging_location,
        'items': [{'sku': x.product.sku, 'product': x.product.name, 'variant': x.product.variant, 'quantity': x.quantity} for x in items]
    }

def seed():
    if Product.query.count():
        return
    products = [
        Product(sku='SHOE101', name='Running Shoes', variant='Black / Size 9', category='Footwear', price=2499),
        Product(sku='TS102', name='Blue T-Shirt', variant='Medium', category='Apparel', price=799),
        Product(sku='BAG103', name='Laptop Bag', variant='15-inch Black', category='Bags', price=1499),
        Product(sku='JEAN104', name='Black Jeans', variant='32 Regular', category='Apparel', price=1299),
        Product(sku='MUG105', name='Travel Mug', variant='500ml Steel', category='Home', price=599),
        Product(sku='CAP106', name='Sports Cap', variant='Black', category='Accessories', price=399),
    ]
    db.session.add_all(products); db.session.flush()
    inv = [
        Inventory(product_id=products[0].id, warehouse='Main', quantity=0, location='A-03-S02'),
        Inventory(product_id=products[0].id, warehouse='Secondary', quantity=8, location='SEC-A-01'),
        Inventory(product_id=products[1].id, warehouse='Main', quantity=15, location='B-02-S04'),
        Inventory(product_id=products[1].id, warehouse='Secondary', quantity=8, location='SEC-B-02'),
        Inventory(product_id=products[2].id, warehouse='Main', quantity=2, location='C-01-S01'),
        Inventory(product_id=products[2].id, warehouse='Secondary', quantity=0, location='SEC-C-01'),
        Inventory(product_id=products[3].id, warehouse='Main', quantity=0, location='D-01-S03'),
        Inventory(product_id=products[3].id, warehouse='Secondary', quantity=0, location='SEC-D-01'),
        Inventory(product_id=products[4].id, warehouse='Main', quantity=20, location='E-02-S01'),
        Inventory(product_id=products[5].id, warehouse='Main', quantity=6, location='F-01-S02'),
    ]
    db.session.add_all(inv); db.session.flush()
    now = datetime.now()
    orders = [
        Order(order_number='ORD-1024', customer_name='Priya Sharma', priority='High', status='Received', deadline=now + timedelta(hours=1), courier='Delhivery'),
        Order(order_number='ORD-1025', customer_name='Rahul Kumar', priority='Normal', status='Picking', deadline=now + timedelta(hours=4), courier='DTDC'),
        Order(order_number='ORD-1026', customer_name='Ananya Rao', priority='High', status='Packing', deadline=now + timedelta(hours=2), courier='BlueDart'),
        Order(order_number='ORD-1027', customer_name='Vikram Singh', priority='Normal', status='Staged', deadline=now + timedelta(hours=5), courier='Delhivery', box_id='BOX-1047', staging_location='STAGE-A-03'),
        Order(order_number='ORD-1028', customer_name='Sneha Patel', priority='High', status='Shipped', deadline=now - timedelta(hours=1), courier='DTDC'),
        Order(order_number='ORD-1029', customer_name='Arjun Mehta', priority='Normal', status='Received', deadline=now + timedelta(hours=6), courier='BlueDart'),
        Order(order_number='ORD-1030', customer_name='Neha Reddy', priority='High', status='Picking', deadline=now + timedelta(minutes=45), courier='Delhivery'),
        Order(order_number='ORD-1031', customer_name='Kiran Das', priority='Normal', status='Packed', deadline=now + timedelta(hours=3), courier='DTDC', box_id='BOX-1051', staging_location='STAGE-B-02'),
    ]
    db.session.add_all(orders); db.session.flush()
    items = [
        OrderItem(order_id=orders[0].id, product_id=products[0].id, quantity=2),
        OrderItem(order_id=orders[1].id, product_id=products[1].id, quantity=2),
        OrderItem(order_id=orders[2].id, product_id=products[2].id, quantity=1),
        OrderItem(order_id=orders[3].id, product_id=products[4].id, quantity=1),
        OrderItem(order_id=orders[4].id, product_id=products[5].id, quantity=1),
        OrderItem(order_id=orders[5].id, product_id=products[3].id, quantity=1),
        OrderItem(order_id=orders[6].id, product_id=products[0].id, quantity=1),
        OrderItem(order_id=orders[7].id, product_id=products[1].id, quantity=1),
    ]
    db.session.add_all(items)
    db.session.add_all([
        Issue(order_id=orders[0].id, issue_type='Stock Missing', description='Main warehouse has no SHOE101. Secondary stock must be transferred.', priority='High'),
        Issue(order_id=orders[5].id, issue_type='Stock Missing', description='JEAN104 is unavailable in both warehouses.', priority='High'),
        Issue(order_id=orders[2].id, issue_type='Courier Risk', description='BlueDart pickup is approaching; packed order must reach staging.', priority='Medium'),
    ])
    db.session.commit()

@app.get('/api/health')
def health(): return jsonify({'status': 'ok'})

@app.get('/api/dashboard')
def dashboard():
    orders = Order.query.all(); now = datetime.now()
    delayed = [o for o in orders if o.status != 'Shipped' and o.deadline < now]
    priority = [o for o in orders if o.priority == 'High' and o.status != 'Shipped']
    status_counts = {}
    for o in orders: status_counts[o.status] = status_counts.get(o.status, 0) + 1
    low_stock = []
    for p in Product.query.all():
        main = db.session.query(func.coalesce(func.sum(Inventory.quantity), 0)).filter(Inventory.product_id == p.id, Inventory.warehouse == 'Main').scalar()
        sec = db.session.query(func.coalesce(func.sum(Inventory.quantity), 0)).filter(Inventory.product_id == p.id, Inventory.warehouse == 'Secondary').scalar()
        if main <= 2 or (main == 0 and sec > 0): low_stock.append({'sku': p.sku, 'name': p.name, 'main': main, 'secondary': sec, 'status': 'Transfer Required' if main == 0 and sec > 0 else 'Low Stock' if main > 0 else 'Out of Stock'})
    return jsonify({'total_orders': len(orders), 'priority_orders': len(priority), 'delayed_orders': len(delayed), 'ready_to_pick': status_counts.get('Received',0), 'ready_to_pack': status_counts.get('Picking',0), 'ready_to_ship': status_counts.get('Staged',0)+status_counts.get('Packed',0), 'status_counts': status_counts, 'urgent_orders': [order_json(o) for o in sorted(priority, key=lambda x:x.deadline)[:5]], 'low_stock': low_stock, 'open_issues': Issue.query.filter_by(status='Open').count()})

@app.get('/api/orders')
def orders():
    status = request.args.get('status'); priority = request.args.get('priority'); q = request.args.get('q','').strip()
    query = Order.query
    if status and status != 'All': query = query.filter_by(status=status)
    if priority and priority != 'All': query = query.filter_by(priority=priority)
    result = query.order_by(Order.deadline.asc()).all()
    if q: result = [o for o in result if q.lower() in (o.order_number + ' ' + o.customer_name).lower() or any(q.lower() in x.product.sku.lower() or q.lower() in x.product.name.lower() for x in OrderItem.query.filter_by(order_id=o.id).all())]
    return jsonify([order_json(o) for o in result])

@app.get('/api/orders/<int:order_id>')
def get_order(order_id):
    o = Order.query.get_or_404(order_id); item = OrderItem.query.filter_by(order_id=o.id).first()
    inventory = []
    for x in OrderItem.query.filter_by(order_id=o.id).all():
        rows = Inventory.query.filter_by(product_id=x.product_id).all()
        inventory.append({'sku': x.product.sku, 'required': x.quantity, 'warehouses': [{'warehouse':r.warehouse,'quantity':r.quantity,'location':r.location} for r in rows]})
    return jsonify({'order': order_json(o), 'inventory': inventory, 'issues': [{'id':i.id,'type':i.issue_type,'description':i.description,'priority':i.priority,'status':i.status} for i in Issue.query.filter_by(order_id=o.id).all()]})

@app.patch('/api/orders/<int:order_id>/status')
def update_status(order_id):
    o = Order.query.get_or_404(order_id); new_status = request.json.get('status')
    allowed = ['Received','Picking','Packed','Staged','Shipped']
    if new_status not in allowed: return jsonify({'error':'Invalid status'}), 400
    o.status = new_status
    if new_status == 'Packed' and not o.box_id: o.box_id = f'BOX-{1000+o.id}'
    if new_status == 'Staged' and not o.staging_location: o.staging_location = f'STAGE-{chr(65+(o.id%3))}-{o.id:02d}'
    db.session.commit(); return jsonify(order_json(o))

@app.post('/api/orders/<int:order_id>/report-issue')
def report_issue(order_id):
    o = Order.query.get_or_404(order_id); data=request.json or {}
    issue=Issue(order_id=o.id, issue_type=data.get('issue_type','Operational Issue'), description=data.get('description',''), priority=data.get('priority','Medium'))
    db.session.add(issue); db.session.commit(); return jsonify({'id':issue.id}), 201

@app.get('/api/inventory')
def inventory():
    result=[]
    for p in Product.query.all():
        rows=Inventory.query.filter_by(product_id=p.id).all(); main=next((r for r in rows if r.warehouse=='Main'),None); sec=next((r for r in rows if r.warehouse=='Secondary'),None)
        total=sum(r.quantity for r in rows)
        status='Transfer Required' if main and main.quantity==0 and sec and sec.quantity>0 else 'Out of Stock' if total==0 else 'Low Stock' if main and main.quantity<=2 else 'Available'
        result.append({'product':product_json(p),'main':main.quantity if main else 0,'main_location':main.location if main else '', 'secondary':sec.quantity if sec else 0,'secondary_location':sec.location if sec else '', 'total':total,'status':status})
    return jsonify(result)

@app.post('/api/transfers')
def create_transfer():
    data=request.json; p=Product.query.filter_by(sku=data.get('sku')).first_or_404(); qty=int(data.get('quantity',0))
    if qty <= 0: return jsonify({'error':'Quantity must be positive'}),400
    src=Inventory.query.filter_by(product_id=p.id, warehouse='Secondary').first(); dst=Inventory.query.filter_by(product_id=p.id, warehouse='Main').first()
    if not src or src.quantity < qty: return jsonify({'error':'Not enough stock in secondary warehouse'}),400
    src.quantity -= qty; dst.quantity += qty
    t=StockTransfer(product_id=p.id, from_warehouse='Secondary', to_warehouse='Main', quantity=qty, status='Completed')
    db.session.add(t); db.session.commit(); return jsonify({'message':'Transfer completed','transfer_id':t.id})

@app.get('/api/transfers')
def transfers():
    return jsonify([{'id':t.id,'sku':t.product.sku,'product':t.product.name,'quantity':t.quantity,'from':t.from_warehouse,'to':t.to_warehouse,'status':t.status,'created_at':iso(t.created_at)} for t in StockTransfer.query.order_by(StockTransfer.created_at.desc()).all()])

@app.get('/api/issues')
def issues():
    return jsonify([{'id':i.id,'order':i.order.order_number if i.order else '-', 'issue_type':i.issue_type,'description':i.description,'priority':i.priority,'status':i.status,'created_at':iso(i.created_at)} for i in Issue.query.order_by(Issue.created_at.desc()).all()])

@app.patch('/api/issues/<int:issue_id>/resolve')
def resolve_issue(issue_id):
    i=Issue.query.get_or_404(issue_id); i.status='Resolved'; i.resolved_at=datetime.now(); db.session.commit(); return jsonify({'message':'Issue resolved'})

@app.get('/api/shipments')
def shipments():
    # Generate today's pickup groups from orders for a simple demo view.
    groups={}
    base=datetime.now().replace(second=0,microsecond=0)
    times={'Delhivery':base+timedelta(hours=1),'DTDC':base+timedelta(hours=2),'BlueDart':base+timedelta(hours=3)}
    for o in Order.query.filter(Order.status.in_(['Packed','Staged','Shipped'])).all():
        g=groups.setdefault(o.courier, {'courier':o.courier,'pickup_time':times.get(o.courier,base+timedelta(hours=2)),'orders':0,'ready':0,'shipped':0})
        g['orders']+=1; g['shipped']+=1 if o.status=='Shipped' else 0; g['ready']+=1 if o.status in ['Packed','Staged'] else 0
    for c,t in times.items(): groups.setdefault(c, {'courier':c,'pickup_time':t,'orders':0,'ready':0,'shipped':0})
    return jsonify([{'courier':g['courier'],'pickup_time':iso(g['pickup_time']),'orders':g['orders'],'ready':g['ready'],'shipped':g['shipped'],'status':'Completed' if g['orders'] and g['ready']==0 else 'Upcoming'} for g in groups.values()])

@app.post('/api/seed-reset')
def seed_reset():
    db.drop_all(); db.create_all(); seed(); return jsonify({'message':'Database reset'})

with app.app_context():
    db.create_all(); seed()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
